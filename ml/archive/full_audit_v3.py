"""
full_audit_v3.py — Comprehensive v3 shortcut audit (Sections A-E).
Run from SIH-2026/:
    conda activate ml && python ml/full_audit_v3.py
"""
import warnings, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, precision_score, recall_score
from sklearn.tree import DecisionTreeClassifier
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

FORBIDDEN = {"scenario_id","is_illicit","pattern_type","is_licit_exchange","split"}

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def histogram_overlap(a, b, n_bins=50):
    lo, hi = min(a.min(), b.min()), max(a.max(), b.max())
    if lo == hi: return 100.0
    bins = np.linspace(lo, hi, n_bins + 1)
    ha, _ = np.histogram(a, bins=bins, density=True)
    hb, _ = np.histogram(b, bins=bins, density=True)
    bin_w = bins[1] - bins[0]
    return float(np.minimum(ha, hb).sum() * bin_w * 100)

# Load
sep("LOADING DATA")
feats_tr = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_te = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_tr  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_te  = pd.read_csv(DATA / "scenario_labels_test.csv")
train = feats_tr.merge(lbls_tr, on="scenario_id")
test  = feats_te.merge(lbls_te, on="scenario_id")
feature_cols = [c for c in feats_tr.columns if c not in FORBIDDEN]
print(f"  {len(feature_cols)} model features | Train: {len(train):,} | Test: {len(test):,}")
X_tr = train[feature_cols].values; y_tr = train["is_illicit"].values
X_te = test[feature_cols].values;  y_te = test["is_illicit"].values

# ---- SECTION A: Single-feature AUC for all features ----
sep("A. SINGLE-FEATURE AUC (all features)")

def single_feat_stats(tr_col, te_col, y_te_arr):
    auc_p = roc_auc_score(y_te_arr, te_col)
    auc_n = roc_auc_score(y_te_arr, -te_col)
    if auc_p >= auc_n:
        auc, dirn, vals_te = auc_p, "higher->illicit", te_col
        vals_tr = tr_col
    else:
        auc, dirn, vals_te = auc_n, "lower->illicit",  -te_col
        vals_tr = -tr_col
    thrs = np.percentile(vals_tr, np.arange(5, 96, 5))
    best_ba, best_thr = 0.0, 0.0
    for thr in thrs:
        pred = (vals_te >= thr).astype(int)
        ba = balanced_accuracy_score(y_te_arr, pred)
        if ba > best_ba: best_ba = ba; best_thr = thr
    preds = (vals_te >= best_thr).astype(int)
    prec = precision_score(y_te_arr, preds, zero_division=0)
    rec  = recall_score(y_te_arr,  preds, zero_division=0)
    return auc, best_thr, dirn, best_ba, prec, rec

rows_a = []
for i, feat in enumerate(feature_cols):
    auc, thr, dirn, ba, prec, rec = single_feat_stats(X_tr[:,i], X_te[:,i], y_te)
    rows_a.append(dict(feature=feat, auc=round(auc,4), best_threshold=round(thr,4),
                       direction=dirn, balanced_acc=round(ba,4),
                       precision=round(prec,4), recall=round(rec,4)))

sf = pd.DataFrame(rows_a).sort_values("auc", ascending=False).reset_index(drop=True)
print(sf.to_string(index=False))
best_f = sf.iloc[0]
print(f"\n  Best single feature: '{best_f['feature']}' AUC={best_f['auc']:.4f}")
if   best_f["auc"] >= 0.97: print("  *** ALERT: >=0.97 — possible shortcut ***")
elif best_f["auc"] >= 0.90: print("  *** WARNING: >=0.90 — inspect distribution ***")
else:                        print("  No feature exceeds 0.90 AUC.")

sf.to_markdown(index=False)
(OUT/"binary_single_feature_audit_v3.md").write_text(
    f"# Single-Feature AUC Audit — v3\n\n{sf.to_markdown(index=False)}\n\n"
    f"**Best:** `{best_f['feature']}` AUC={best_f['auc']:.4f}\n")
print(f"  Saved: {OUT/'binary_single_feature_audit_v3.md'}")

# ---- SECTION B: Pairwise / simple-rule audit ----
sep("B. SIMPLE-RULE / PAIRWISE AUDIT")
pairs = [
    ("time_span_hours","num_txns"), ("time_span_hours","unique_ip_count"),
    ("num_txns","unique_ip_count"), ("num_txns","unique_input_addrs"),
    ("unique_ip_count","unique_input_addrs"), ("address_reuse_ratio","edge_to_node_ratio"),
    ("fanout_ratio","fanin_ratio"), ("inter_tx_delta_mean","inter_tx_delta_std"),
    ("max_chain_length","max_in_degree"), ("graph_density","avg_clustering"),
    ("total_input_mean","total_output_mean"), ("inter_tx_delta_min","burstiness_B"),
    (sf.iloc[0]["feature"], sf.iloc[1]["feature"]),
    (sf.iloc[0]["feature"], sf.iloc[2]["feature"]),
]
seen_pairs = set(); pairs_clean = []
for a, b in pairs:
    key = tuple(sorted([a,b]))
    if key not in seen_pairs and a in feature_cols and b in feature_cols and a != b:
        seen_pairs.add(key); pairs_clean.append((a,b))

rule_rows = []
for fa, fb in pairs_clean:
    ia, ib = feature_cols.index(fa), feature_cols.index(fb)
    Xp_tr = X_tr[:,[ia,ib]]; Xp_te = X_te[:,[ia,ib]]
    for depth in [1,2]:
        dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
        dt.fit(Xp_tr, y_tr)
        proba = dt.predict_proba(Xp_te)[:,1]
        auc   = roc_auc_score(y_te, proba)
        ba    = balanced_accuracy_score(y_te, dt.predict(Xp_te))
        rule_rows.append(dict(feature_a=fa, feature_b=fb, depth=depth,
                              auc=round(auc,4), balanced_acc=round(ba,4)))

rule_df = pd.DataFrame(rule_rows).sort_values("auc",ascending=False)
print(rule_df.to_string(index=False))
best_r = rule_df.iloc[0]
tag = ("*** ALERT ***" if best_r["auc"]>=0.97 else
       "WARNING"      if best_r["auc"]>=0.90 else "OK")
print(f"\n  Best pairwise rule: {best_r['feature_a']}+{best_r['feature_b']} depth={best_r['depth']} AUC={best_r['auc']:.4f}  [{tag}]")
(OUT/"binary_simple_rule_audit_v3.md").write_text(
    f"# Simple-Rule Audit — v3\n\n{rule_df.to_markdown(index=False)}\n\n"
    f"**Best:** `{best_r['feature_a']}` + `{best_r['feature_b']}` depth={best_r['depth']} AUC={best_r['auc']:.4f}\n")
print(f"  Saved: {OUT/'binary_simple_rule_audit_v3.md'}")

# ---- SECTION C: Leakage audit ----
sep("C. LEAKAGE / DERIVATION AUDIT")
print("  Hard-excluded (verified absent from feature matrix):")
for col in ["is_illicit","pattern_type","is_licit_exchange"]:
    present = col in list(feats_tr.columns)
    print(f"    {col}: {'PRESENT — LEAKAGE' if present else 'ABSENT — OK'}")

sidx = feature_cols.index("suspicious_infra_ratio")
susp_auc = max(roc_auc_score(y_te,X_te[:,sidx]), roc_auc_score(y_te,-X_te[:,sidx]))
licit_s   = X_tr[y_tr==0, sidx]; illicit_s = X_tr[y_tr==1, sidx]
ov_s = histogram_overlap(licit_s, illicit_s)
print(f"\n  suspicious_infra_ratio: AUC={susp_auc:.4f} | overlap={ov_s:.1f}%")
print(f"    Licit mean={licit_s.mean():.3f} | Illicit mean={illicit_s.mean():.3f}")
if susp_auc >= 0.90:
    print("    *** Possibly reflects generator-level label bias — inspect ***")
else:
    print("    AUC within acceptable range.")

# ---- SECTION D: Full correlation matrix ----
sep("D. FULL CORRELATION MATRIX")
df_feat = pd.DataFrame(X_tr, columns=feature_cols)
corr = df_feat.corr()
high_corr = []
for i in range(len(feature_cols)):
    for j in range(i+1, len(feature_cols)):
        r = corr.iloc[i,j]
        if abs(r) > 0.80:
            high_corr.append((feature_cols[i], feature_cols[j], round(r,3)))
hc_df = pd.DataFrame(high_corr, columns=["feature_1","feature_2","r"])
hc_df = hc_df.iloc[hc_df["r"].abs().argsort()[::-1]]
print(f"  {len(hc_df)} pairs with |r|>0.80:")
print(hc_df.to_string(index=False))

fig, ax = plt.subplots(figsize=(14,13))
im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="RdBu_r", aspect="auto")
n = len(feature_cols)
ax.set_xticks(range(n)); ax.set_yticks(range(n))
ax.set_xticklabels(feature_cols, rotation=90, fontsize=5.5)
ax.set_yticklabels(feature_cols, fontsize=5.5)
plt.colorbar(im, ax=ax, shrink=0.6)
ax.set_title("Full Feature Correlation Matrix — v3", fontweight="bold")
plt.tight_layout(); fig.savefig(OUT/"diag_corr_full_v3.png", dpi=120); plt.close()
print(f"  Saved: {OUT/'diag_corr_full_v3.png'}")

# ---- SECTION E: Distribution overlap ----
sep("E. DISTRIBUTION OVERLAP")
key_feats = ["time_span_hours","num_txns","unique_ip_count","unique_input_addrs",
             "unique_asn_count","inter_tx_delta_mean","inter_tx_delta_std",
             "inter_tx_delta_min","burstiness_B","total_input_mean","output_amount_gini",
             "amount_decay_slope","graph_density","max_chain_length",
             "address_reuse_ratio","edge_to_node_ratio","fanout_ratio","fanin_ratio",
             "max_in_degree","suspicious_infra_ratio"]
key_feats = [f for f in key_feats if f in feature_cols]

ov_rows = []
for feat in key_feats:
    idx = feature_cols.index(feat)
    lv = X_tr[y_tr==0, idx]; iv = X_tr[y_tr==1, idx]
    ov = histogram_overlap(lv, iv)
    auc_v = max(roc_auc_score(y_te,X_te[:,idx]), roc_auc_score(y_te,-X_te[:,idx]))
    ov_rows.append(dict(feature=feat, licit_med=round(np.median(lv),3),
                        illicit_med=round(np.median(iv),3),
                        overlap_pct=round(ov,1), auc=round(auc_v,4)))
ov_df = pd.DataFrame(ov_rows).sort_values("overlap_pct")
print(ov_df.to_string(index=False))

fig, axes = plt.subplots(5, 4, figsize=(16,18))
axes = axes.flatten()
for i, row in enumerate(ov_df.itertuples()):
    if i >= len(axes): break
    feat = row.feature; idx = feature_cols.index(feat)
    lv = X_tr[y_tr==0, idx]; iv = X_tr[y_tr==1, idx]
    ax = axes[i]
    lo = min(np.percentile(lv,1),np.percentile(iv,1))
    hi = max(np.percentile(lv,99),np.percentile(iv,99))
    bins = np.linspace(lo,hi,40)
    ax.hist(lv, bins=bins, alpha=0.5, color="#4A90D9", density=True, label="licit")
    ax.hist(iv, bins=bins, alpha=0.5, color="#E8504A", density=True, label="illicit")
    ax.set_title(f"{feat}\n{row.overlap_pct:.0f}% overlap | AUC={row.auc:.3f}",
                 fontsize=7, fontweight="bold")
    ax.tick_params(labelsize=6)
    if i == 0: ax.legend(fontsize=6)
for j in range(i+1, len(axes)): axes[j].set_visible(False)
plt.suptitle("Licit vs Illicit Distributions — v3", fontsize=11, fontweight="bold")
plt.tight_layout(); fig.savefig(OUT/"diag_dist_overlap_v3.png", dpi=120); plt.close()
print(f"  Saved: {OUT/'diag_dist_overlap_v3.png'}")

# ---- FINAL SUMMARY ----
sep("AUDIT SUMMARY")
print(f"""
A. Single-feature AUC:
   Best  : {sf.iloc[0]['feature']} (AUC={sf.iloc[0]['auc']:.4f})
   2nd   : {sf.iloc[1]['feature']} (AUC={sf.iloc[1]['auc']:.4f})
   3rd   : {sf.iloc[2]['feature']} (AUC={sf.iloc[2]['auc']:.4f})
   Near-perfect (>=0.97)? {'YES — INVESTIGATE' if sf.iloc[0]['auc'] >= 0.97 else 'NO'}
   Strong (>=0.90)?       {'YES — INSPECT' if sf.iloc[0]['auc'] >= 0.90 else 'NO'}

B. Best pairwise rule:
   {best_r['feature_a']} + {best_r['feature_b']} depth={best_r['depth']} AUC={best_r['auc']:.4f}
   Near-perfect (>=0.97)? {'YES' if best_r['auc'] >= 0.97 else 'NO'}

C. Leakage: is_illicit, pattern_type, is_licit_exchange absent from feature matrix.
   suspicious_infra_ratio AUC: {susp_auc:.4f} overlap: {ov_s:.1f}%

D. Correlated pairs (|r|>0.80): {len(hc_df)}
   Highest: {hc_df.iloc[0]['feature_1']} <-> {hc_df.iloc[0]['feature_2']} r={hc_df.iloc[0]['r']:.3f}

E. Lowest overlap feature: {ov_df.iloc[0]['feature']} ({ov_df.iloc[0]['overlap_pct']:.1f}%)
   All features >=10% overlap? {'YES' if ov_df['overlap_pct'].min() >= 10.0 else 'NO — ' + str(ov_df[ov_df['overlap_pct']<10]['feature'].tolist())}
""")
