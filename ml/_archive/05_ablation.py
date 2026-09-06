"""
05_ablation.py — Feature-group ablation study.
Configurations:
  (1) Blockchain-only (amount + structural + temporal from blockchain txns)
  (2) Network-only    (propagation + network metadata from network_metadata)
  (3) Combined-no-graph (Phase-1 features; blockchain + network, no graph)
  (4) Full            (all 46 features including graph)

Run from SIH-2026/:
    conda activate ml && python ml/05_ablation.py
"""
import json, warnings
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
MDLS = ROOT / "ml" / "models"
OUT.mkdir(parents=True, exist_ok=True)

FORBIDDEN = {"scenario_id","is_illicit","pattern_type","is_licit_exchange","split"}

# Feature groups — derived from 02_feature_engineering.py structure
BLOCKCHAIN_FEATS = [
    # Amount
    "total_input_mean","total_output_mean","fee_ratio_mean","fee_ratio_std",
    "amount_decay_slope","output_amount_gini","denomination_entropy",
    "round_number_ratio","io_amount_similarity",
    # Structural
    "num_txns","mean_num_inputs","mean_num_outputs","io_count_ratio",
    "unique_input_addrs","unique_output_addrs","address_reuse_ratio",
    "change_output_ratio","script_type_entropy","script_type_mode",
    # Temporal
    "time_span_hours","inter_tx_delta_mean","inter_tx_delta_std",
    "inter_tx_delta_min","burstiness_B","hour_of_day_entropy",
]
NETWORK_FEATS = [
    # Propagation (relay_timestamp vs blockchain timestamp)
    "prop_delta_mean","prop_delta_std","prop_delta_cv",
    # Network metadata
    "suspicious_infra_ratio","unique_asn_count","asn_concentration",
    "unique_country_count","country_concentration","unique_ip_count",
    "ip_to_addr_ratio","alt_port_ratio","unique_user_agents",
]
GRAPH_FEATS = [
    "max_chain_length","graph_density","avg_clustering",
    "max_in_degree","max_out_degree","degree_assortativity","edge_to_node_ratio",
]

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

sep("LOADING DATA")
feats_tr = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_te = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_tr  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_te  = pd.read_csv(DATA / "scenario_labels_test.csv")
train = feats_tr.merge(lbls_tr, on="scenario_id")
test  = feats_te.merge(lbls_te, on="scenario_id")

all_feature_cols = [c for c in feats_tr.columns if c not in FORBIDDEN]
y_tr = train["is_illicit"].values
y_te = test["is_illicit"].values

# Scale pos weight from actual v3 labels
n_licit   = (y_tr == 0).sum()
n_illicit = (y_tr == 1).sum()
spw = n_licit / n_illicit
print(f"  scale_pos_weight (v3): {spw:.4f}  ({n_licit} licit / {n_illicit} illicit)")

def available(feat_list):
    return [f for f in feat_list if f in all_feature_cols]

configs = {
    "blockchain-only":   available(BLOCKCHAIN_FEATS),
    "network-only":      available(NETWORK_FEATS),
    "combined-no-graph": available(BLOCKCHAIN_FEATS + NETWORK_FEATS),
    "full":              all_feature_cols,
}

for name, cols in configs.items():
    print(f"  Config '{name}': {len(cols)} features")

def train_eval(feat_list, y_tr, y_te, spw, name):
    X_tr = train[feat_list].values
    X_te = test[feat_list].values
    m = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
        scale_pos_weight=spw, tree_method="hist",
        random_state=42, verbosity=0,
    )
    m.fit(X_tr, y_tr)
    proba = m.predict_proba(X_te)[:,1]
    preds = (proba >= 0.5).astype(int)
    roc  = roc_auc_score(y_te, proba)
    pr   = average_precision_score(y_te, proba)
    f1   = f1_score(y_te, preds)
    prec = precision_score(y_te, preds, zero_division=0)
    rec  = recall_score(y_te,  preds, zero_division=0)
    print(f"  [{name}]  ROC={roc:.4f}  PR={pr:.4f}  F1={f1:.4f}  P={prec:.4f}  R={rec:.4f}")
    return dict(config=name, n_feats=len(feat_list),
                roc_auc=round(roc,4), pr_auc=round(pr,4),
                f1=round(f1,4), precision=round(prec,4), recall=round(rec,4))

sep("RUNNING ABLATION")
results = []
for name, cols in configs.items():
    res = train_eval(cols, y_tr, y_te, spw, name)
    results.append(res)

df = pd.DataFrame(results)
print(f"\n  ABLATION RESULTS:")
print(df.to_string(index=False))

# Compute deltas vs blockchain-only (baseline)
baseline_roc = df[df["config"]=="blockchain-only"]["roc_auc"].values[0]
full_roc     = df[df["config"]=="full"]["roc_auc"].values[0]
net_roc      = df[df["config"]=="network-only"]["roc_auc"].values[0]
no_g_roc     = df[df["config"]=="combined-no-graph"]["roc_auc"].values[0]
print(f"\n  Absolute improvements over blockchain-only:")
print(f"    + Network-only vs baseline:   {net_roc - baseline_roc:+.4f}")
print(f"    + Combined-no-graph vs base:  {no_g_roc - baseline_roc:+.4f}")
print(f"    + Full vs blockchain-only:    {full_roc - baseline_roc:+.4f}")
print(f"    Graph contribution (full - no_graph): {full_roc - no_g_roc:+.4f}")

# Bar chart
fig, ax = plt.subplots(figsize=(10,5))
colors = ["#B0C4DE","#E8904A","#5DA85D","#4A90D9"]
x = np.arange(len(df))
bars = ax.bar(x, df["roc_auc"], color=colors, alpha=0.85, width=0.5)
for bar, val in zip(bars, df["roc_auc"]):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.002,
            f"{val:.4f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(df["config"], fontsize=10)
ax.set_ylabel("ROC-AUC"); ax.set_title("Ablation Study — Binary Model (v3)", fontweight="bold")
ax.set_ylim(max(0, df["roc_auc"].min()-0.05), min(1.01, df["roc_auc"].max()+0.03))
# Second metric (F1)
ax2 = ax.twinx()
ax2.plot(x, df["f1"], "k--o", alpha=0.5, label="F1")
ax2.set_ylabel("F1", alpha=0.5)
ax2.legend(loc="lower right")
plt.tight_layout(); fig.savefig(OUT/"ablation_results_v3.png", dpi=150); plt.close()
print(f"  Saved: {OUT/'ablation_results_v3.png'}")

# Markdown
md = ["# Ablation Results — v3\n",
      f"\n**scale_pos_weight:** {spw:.4f} (computed from v3 train labels)\n",
      f"\n{df.to_markdown(index=False)}\n",
      f"\n## Deltas\n",
      f"- Network-only vs blockchain-only: {net_roc-baseline_roc:+.4f}",
      f"- Combined-no-graph vs blockchain-only: {no_g_roc-baseline_roc:+.4f}",
      f"- Full vs blockchain-only: {full_roc-baseline_roc:+.4f}",
      f"- Graph contribution (full - combined-no-graph): {full_roc-no_g_roc:+.4f}",
      f"\n## Interpretation",
      f"\n{'Network features improve AUC by ' + f'{full_roc-baseline_roc:+.4f}' if full_roc > baseline_roc else 'Network/graph features do not significantly improve AUC — report honestly.'}"]
(OUT/"ablation_results_v3.md").write_text("\n".join(md))
print(f"  Saved: {OUT/'ablation_results_v3.md'}")
sep("DONE — 05_ablation.py")
