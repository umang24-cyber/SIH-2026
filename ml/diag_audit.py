"""
diag_audit.py — Read-only diagnostic audit on binary_xgb_v1.
No saved models are modified. Throwaway comparison models are trained
in-memory only and discarded after metrics are reported.

Run from SIH-2026/:
    conda activate ml
    python ml/diag_audit.py
"""

import json, warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import logit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
MDLS = ROOT / "ml" / "models"

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ---------------------------------------------------------------------------
# Load data + model meta
# ---------------------------------------------------------------------------
sep("LOADING DATA")
feats_tr = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_te = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_tr  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_te  = pd.read_csv(DATA / "scenario_labels_test.csv")

train = feats_tr.merge(lbls_tr, on="scenario_id")
test  = feats_te.merge(lbls_te, on="scenario_id")

with open(MDLS / "binary_model_meta.json") as f:
    meta = json.load(f)

feature_cols = meta["feature_cols"]   # exact same list used during training
spw          = meta["scale_pos_weight"]

FORBIDDEN = {"is_illicit", "pattern_type", "scenario_id"}
X_tr_full = train[feature_cols].values
y_tr      = train["is_illicit"].values
X_te_full = test[feature_cols].values
y_te      = test["is_illicit"].values

print(f"  Train: {X_tr_full.shape}  Test: {X_te_full.shape}")
print(f"  scale_pos_weight from meta: {spw:.4f}")

# ---------------------------------------------------------------------------
# Helper: fast XGBoost refit (same hyperparams, no early stopping for speed)
# Using n_estimators=200 (good enough for diagnostic AUC, 3× faster)
# ---------------------------------------------------------------------------
def quick_xgb(X_tr, y_tr, spw):
    m = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
        scale_pos_weight=spw, tree_method="hist",
        random_state=42, verbosity=0,
    )
    m.fit(X_tr, y_tr)
    return m

# ---------------------------------------------------------------------------
# TASK 1 — Single-feature baseline AUC
# ---------------------------------------------------------------------------
sep("TASK 1 — SINGLE-FEATURE BASELINE AUC")

def single_feat_auc(feat_name, X_tr_col, y_tr, X_te_col, y_te, label):
    """Logistic regression on one feature → AUC (both directions)."""
    lr = LogisticRegression(random_state=42, max_iter=500)
    lr.fit(X_tr_col.reshape(-1,1), y_tr)
    prob = lr.predict_proba(X_te_col.reshape(-1,1))[:,1]
    auc_lr = roc_auc_score(y_te, prob)
    # Also raw threshold sweep (sign doesn't matter for AUC)
    auc_raw = max(roc_auc_score(y_te, X_te_col),
                  roc_auc_score(y_te, -X_te_col))
    print(f"  {label}:")
    print(f"    Threshold sweep AUC : {auc_raw:.6f}")
    print(f"    LogReg AUC          : {auc_lr:.6f}")
    return auc_raw, auc_lr

idx_tsh = feature_cols.index("time_span_hours")
idx_asn = feature_cols.index("unique_asn_count")

auc_tsh_raw, auc_tsh_lr = single_feat_auc(
    "time_span_hours", X_tr_full[:,idx_tsh], y_tr,
    X_te_full[:,idx_tsh], y_te, "time_span_hours only")

auc_asn_raw, auc_asn_lr = single_feat_auc(
    "unique_asn_count", X_tr_full[:,idx_asn], y_tr,
    X_te_full[:,idx_asn], y_te, "unique_asn_count only")

# Pair: {time_span_hours, unique_asn_count}
pair_cols = [idx_tsh, idx_asn]
lr_pair = LogisticRegression(random_state=42, max_iter=500)
lr_pair.fit(X_tr_full[:, pair_cols], y_tr)
prob_pair = lr_pair.predict_proba(X_te_full[:, pair_cols])[:,1]
auc_pair = roc_auc_score(y_te, prob_pair)
print(f"\n  {{time_span_hours, unique_asn_count}} pair (LogReg):")
print(f"    AUC = {auc_pair:.6f}")

print(f"\n  TASK 1 SUMMARY:")
print(f"    time_span_hours alone  (threshold): {auc_tsh_raw:.6f}")
print(f"    unique_asn_count alone (threshold): {auc_asn_raw:.6f}")
print(f"    pair (LogReg)                     : {auc_pair:.6f}")
if auc_tsh_raw >= 0.98:
    print("  *** ALERT: single feature AUC >= 0.98 — near-perfect threshold rule exists ***")

# ---------------------------------------------------------------------------
# TASK 2 — Leave-feature-out ablation
# ---------------------------------------------------------------------------
sep("TASK 2 — LEAVE-FEATURE-OUT ABLATION")

# (a) Full model — refit with 200 estimators for fair comparison
print("  (a) Full model (200 estimators, same params)...")
m_full = quick_xgb(X_tr_full, y_tr, spw)
auc_full = roc_auc_score(y_te, m_full.predict_proba(X_te_full)[:,1])
print(f"      AUC = {auc_full:.6f}")

# (b) Minus time_span_hours
mask_b = [i for i, c in enumerate(feature_cols) if c != "time_span_hours"]
print(f"  (b) Minus time_span_hours ({len(mask_b)} features)...")
m_b = quick_xgb(X_tr_full[:, mask_b], y_tr, spw)
auc_b = roc_auc_score(y_te, m_b.predict_proba(X_te_full[:, mask_b])[:,1])
print(f"      AUC = {auc_b:.6f}")

# (c) Minus both time_span_hours AND unique_asn_count
mask_c = [i for i, c in enumerate(feature_cols)
          if c not in {"time_span_hours", "unique_asn_count"}]
print(f"  (c) Minus time_span_hours + unique_asn_count ({len(mask_c)} features)...")
m_c = quick_xgb(X_tr_full[:, mask_c], y_tr, spw)
auc_c = roc_auc_score(y_te, m_c.predict_proba(X_te_full[:, mask_c])[:,1])
print(f"      AUC = {auc_c:.6f}")

print(f"\n  TASK 2 SUMMARY:")
print(f"    (a) Full model        : AUC = {auc_full:.6f}")
print(f"    (b) -time_span_hours  : AUC = {auc_b:.6f}  (delta = {auc_b-auc_full:+.6f})")
print(f"    (c) -time + -asn_count: AUC = {auc_c:.6f}  (delta = {auc_c-auc_full:+.6f})")

if auc_c >= 0.90:
    print("  >> GOOD NEWS: AUC stays >=0.90 with both removed — genuine redundant signal across features.")
elif auc_c >= 0.75:
    print("  >> MODERATE: AUC 0.75-0.90 without both — some signal remains but these features are load-bearing.")
else:
    print("  *** CONCERN: AUC collapses below 0.75 — model heavily dependent on 1-2 features. Address before Day 3.")

# ---------------------------------------------------------------------------
# TASK 3 — Correlation matrix of top-10 features by gain
# ---------------------------------------------------------------------------
sep("TASK 3 — TOP-10 FEATURE PAIRWISE CORRELATION")

# Use the full 46-feature model's importances (refit above = m_full)
imp = pd.Series(m_full.feature_importances_, index=feature_cols).sort_values(ascending=False)
top10 = imp.head(10)
print("  Top-10 features by gain:")
total_imp = imp.sum()
for i, (feat, val) in enumerate(top10.items()):
    print(f"    {i+1:2d}. {feat:<35} gain={val:.4f}  share={val/total_imp:.1%}")

top10_cols = [feature_cols.index(f) for f in top10.index]
X_top10_tr = pd.DataFrame(X_tr_full[:, top10_cols], columns=top10.index)
corr = X_top10_tr.corr()

print(f"\n  Pairwise Pearson correlation matrix (top-10):")
pd.set_option("display.float_format", "{:.2f}".format)
pd.set_option("display.max_columns", 10)
pd.set_option("display.width", 120)
print(corr.to_string())

# Flag clusters with |r| > 0.8
print("\n  Feature pairs with |r| > 0.80:")
flagged = False
feats_t10 = list(top10.index)
for i in range(len(feats_t10)):
    for j in range(i+1, len(feats_t10)):
        r = corr.iloc[i, j]
        if abs(r) > 0.80:
            print(f"    {feats_t10[i]:<35} <-> {feats_t10[j]:<35}  r={r:.3f}")
            flagged = True
if not flagged:
    print("    None — top-10 features are relatively independent.")

# Plot correlation heatmap
fig, ax = plt.subplots(figsize=(10, 9))
im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r", aspect="auto")
ax.set_xticks(range(10)); ax.set_yticks(range(10))
ax.set_xticklabels(feats_t10, rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(feats_t10, fontsize=8)
for i in range(10):
    for j in range(10):
        ax.text(j, i, f"{corr.iloc[i,j]:.2f}", ha="center", va="center",
                fontsize=7, color="white" if abs(corr.iloc[i,j]) > 0.6 else "black")
plt.colorbar(im, ax=ax, shrink=0.8)
ax.set_title("Top-10 Feature Pairwise Pearson Correlation", fontweight="bold", fontsize=12)
plt.tight_layout()
fig.savefig(OUT / "diag_top10_corr_heatmap.png", dpi=150)
plt.close()
print(f"\n  Saved: {OUT / 'diag_top10_corr_heatmap.png'}")

# ---------------------------------------------------------------------------
# TASK 4 — time_span_hours distribution sanity check
# ---------------------------------------------------------------------------
sep("TASK 4 — time_span_hours DISTRIBUTION BREAKDOWN")

df_full = train.copy()  # use full train set (has pattern_type from labels join)
# Identify hard-negative exchange scenarios from train blockchain CSV
bc_tr = pd.read_csv(DATA / "train_blockchain.csv",
                    usecols=["scenario_id","pattern_type","is_illicit","txid"])
sc_counts = bc_tr.groupby("scenario_id").agg(
    n_txns=("txid","count"),
    pattern_type=("pattern_type","first"),
    is_illicit=("is_illicit","first")
).reset_index()

exchange_ids = set(
    sc_counts[(sc_counts["is_illicit"]==0) &
              (sc_counts["pattern_type"]=="normal") &
              (sc_counts["scenario_id"].str.startswith("exchange_"))]["scenario_id"]
)
print(f"  Hard-negative exchange scenarios identified: {len(exchange_ids)}")

df_full["is_exchange"] = df_full["scenario_id"].isin(exchange_ids)

print(f"\n  time_span_hours by group (train set):")
print(f"  {'Group':<40} {'N':>6} {'Min':>14} {'Median':>14} {'Max':>14}")
print(f"  {'-'*90}")

groups = [
    ("Hard-negative exchanges (licit)",       df_full[df_full["is_exchange"]]),
    ("Other normal/licit (non-exchange)",     df_full[(df_full["pattern_type"]=="normal") & ~df_full["is_exchange"]]),
    ("Ransomware (illicit)",                  df_full[df_full["pattern_type"]=="ransomware"]),
    ("Peeling chain (illicit)",               df_full[df_full["pattern_type"]=="peeling_chain"]),
    ("Layering (illicit)",                    df_full[df_full["pattern_type"]=="layering"]),
    ("Mixing (illicit)",                      df_full[df_full["pattern_type"]=="mixing"]),
]

stats = {}
for label, grp in groups:
    vals = grp["time_span_hours"]
    n    = len(vals)
    if n == 0:
        print(f"  {label:<40} {'0':>6}")
        continue
    mn, med, mx = vals.min(), vals.median(), vals.max()
    stats[label] = (n, mn, med, mx)
    print(f"  {label:<40} {n:>6,} {mn:>14.2f} {med:>14.2f} {mx:>14.2f}")

# Key question: does the gap hold even excluding exchanges?
other_normal = df_full[(df_full["pattern_type"]=="normal") & ~df_full["is_exchange"]]
illicit_all  = df_full[df_full["is_illicit"]==1]
if len(other_normal) > 0 and len(illicit_all) > 0:
    gap_min_licit   = other_normal["time_span_hours"].min()
    gap_max_illicit = illicit_all["time_span_hours"].max()
    print(f"\n  Gap analysis (exchanges excluded):")
    print(f"    Licit non-exchange   min time_span: {gap_min_licit:.2f} hours")
    print(f"    Illicit (all)        max time_span: {gap_max_illicit:.2f} hours")
    if gap_min_licit > gap_max_illicit:
        print(f"    >> COMPLETE SEPARATION even without exchanges — gap = {gap_min_licit - gap_max_illicit:.2f} hrs")
        print(f"    >> The gap is NOT driven by exchanges alone; all normal scenarios are long-running.")
    else:
        print(f"    >> Overlap exists without exchanges — separation requires the exchange scenarios.")

# Plot: log-scale violin / strip by group
fig, ax = plt.subplots(figsize=(12, 5))
colors = {"exchange": "#4A90D9", "normal_bg": "#82C882",
          "ransomware": "#E8504A", "peeling_chain": "#F4A460",
          "layering": "#DDA0DD", "mixing": "#FF8C8C"}
plot_data = [
    ("Exchanges\n(licit)", df_full[df_full["is_exchange"]]["time_span_hours"], "#4A90D9"),
    ("Normal bg\n(licit)", df_full[(df_full["pattern_type"]=="normal") & ~df_full["is_exchange"]]["time_span_hours"], "#82C882"),
    ("Ransomware", df_full[df_full["pattern_type"]=="ransomware"]["time_span_hours"], "#E8504A"),
    ("Peeling\nchain", df_full[df_full["pattern_type"]=="peeling_chain"]["time_span_hours"], "#F4A460"),
    ("Layering", df_full[df_full["pattern_type"]=="layering"]["time_span_hours"], "#DDA0DD"),
    ("Mixing", df_full[df_full["pattern_type"]=="mixing"]["time_span_hours"], "#FF8C8C"),
]
for i, (lbl, vals, col) in enumerate(plot_data):
    if len(vals) == 0: continue
    # jitter strip
    jitter = np.random.default_rng(i).uniform(-0.2, 0.2, size=min(len(vals), 500))
    sample = vals.sample(min(len(vals), 500), random_state=i)
    ax.scatter(np.full(len(sample), i) + jitter, np.log1p(sample),
               color=col, alpha=0.3, s=8, rasterized=True)
    # median line
    ax.hlines(np.log1p(vals.median()), i-0.35, i+0.35,
              colors=col, linewidth=3, label=f"{lbl} med={vals.median():.1f}h")

ax.set_xticks(range(len(plot_data)))
ax.set_xticklabels([d[0] for d in plot_data], fontsize=10)
ax.set_ylabel("log1p(time_span_hours)")
ax.set_title("Scenario Duration Distribution by Group (log scale, train set)",
             fontweight="bold")
plt.tight_layout()
fig.savefig(OUT / "diag_duration_by_group.png", dpi=150)
plt.close()
print(f"\n  Saved: {OUT / 'diag_duration_by_group.png'}")

# ---------------------------------------------------------------------------
# FINAL DIAGNOSTIC SUMMARY
# ---------------------------------------------------------------------------
sep("DIAGNOSTIC SUMMARY")
print(f"""
  TASK 1 — Single-feature AUC:
    time_span_hours alone  (threshold sweep): {auc_tsh_raw:.6f}
    unique_asn_count alone (threshold sweep): {auc_asn_raw:.6f}
    {{time_span_hours, unique_asn_count}} pair: {auc_pair:.6f}

  TASK 2 — Leave-feature-out AUC:
    (a) Full model (46 features)            : {auc_full:.6f}
    (b) -time_span_hours (45 features)      : {auc_b:.6f}   delta={auc_b-auc_full:+.6f}
    (c) -time_span -unique_asn (44 features): {auc_c:.6f}   delta={auc_c-auc_full:+.6f}

  TASK 3 — top-10 correlation: see diag_top10_corr_heatmap.png
  TASK 4 — duration breakdown: see diag_duration_by_group.png
""")
