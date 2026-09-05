import json, pickle, warnings, os, subprocess
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score,
    roc_auc_score, average_precision_score, brier_score_loss
)
from sklearn.model_selection import StratifiedShuffleSplit, StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MDLS = ROOT / "ml" / "models"
REPS = ROOT / "ml" / "reports"
MANS = ROOT / "ml" / "manifests"
LOGS = ROOT / "ml" / "logs"

for d in [MDLS, REPS, MANS, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

FORBIDDEN_FEATURES = {"is_illicit", "pattern_type", "scenario_id", "split", "is_licit_exchange"}
TYPOLOGIES = ["ransomware", "peeling_chain", "layering", "mixing"]

def ece_score(y_true, y_prob, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0; n = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() > 0:
            ece += mask.sum() / n * abs(y_true[mask].mean() - y_prob[mask].mean())
    return float(ece)

print("==================================================")
print("1. LOADING V6 FROZEN DATA")
print("==================================================")
feats_tr = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_te = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_tr  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_te  = pd.read_csv(DATA / "scenario_labels_test.csv")

train_all = feats_tr.merge(lbls_tr, on="scenario_id")
test_all  = feats_te.merge(lbls_te, on="scenario_id")

print("==================================================")
print("2. VALIDATING FEATURE MATRIX & SPLIT")
print("==================================================")
# Check intersection
train_scen = set(train_all["scenario_id"])
test_scen = set(test_all["scenario_id"])
assert len(train_scen & test_scen) == 0, "FATAL: Train/Test scenario leakage!"
print(f"Train scenarios: {len(train_scen)}, Test scenarios: {len(test_scen)}")
print(f"Intersection: 0")

feature_cols = [c for c in feats_tr.columns if c not in FORBIDDEN_FEATURES]
for col in ["is_illicit", "pattern_type", "scenario_id", "split", "is_licit_exchange"]:
    assert col not in feature_cols, f"FATAL: {col} leaked into feature matrix!"

# Also assert missing values
assert train_all[feature_cols].isna().sum().sum() == 0, "FATAL: NaNs in train"
assert test_all[feature_cols].isna().sum().sum() == 0, "FATAL: NaNs in test"
print(f"Feature columns ({len(feature_cols)}): {feature_cols}")

print("==================================================")
print("3. BINARY MODEL TRAINING (PHASE 4)")
print("==================================================")
X_tr = train_all[feature_cols].values
y_tr = train_all["is_illicit"].values
X_te = test_all[feature_cols].values
y_te = test_all["is_illicit"].values

# Same splitting logic as 03_train_binary.py
sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
idx_proper, idx_holdout = next(sss1.split(X_tr, y_tr))
X_proper, y_proper = X_tr[idx_proper], y_tr[idx_proper]
X_holdout, y_holdout = X_tr[idx_holdout], y_tr[idx_holdout]
sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
idx_eval, idx_cal = next(sss2.split(X_holdout, y_holdout))
X_eval, y_eval = X_holdout[idx_eval], y_holdout[idx_eval]

scale_pos_weight = (y_tr == 0).sum() / (y_tr == 1).sum()

bin_model = XGBClassifier(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
    scale_pos_weight=scale_pos_weight, eval_metric="logloss",
    early_stopping_rounds=50, tree_method="hist", random_state=42, verbosity=0
)
bin_model.fit(X_proper, y_proper, eval_set=[(X_eval, y_eval)], verbose=False)
bin_model.save_model(MDLS / "binary_model_v7_candidate.xgb")

y_te_prob = bin_model.predict_proba(X_te)[:,1]
y_te_pred = bin_model.predict(X_te)
bin_metrics = {
    "roc_auc": roc_auc_score(y_te, y_te_prob),
    "pr_auc": average_precision_score(y_te, y_te_prob),
    "accuracy": accuracy_score(y_te, y_te_pred),
    "bacc": balanced_accuracy_score(y_te, y_te_pred),
    "f1": f1_score(y_te, y_te_pred),
    "precision": precision_score(y_te, y_te_pred),
    "recall": recall_score(y_te, y_te_pred)
}
print(bin_metrics)

print("==================================================")
print("4. BINARY FEATURE IMPORTANCE (PHASE 5)")
print("==================================================")
bin_gain = pd.Series(bin_model.feature_importances_, index=feature_cols).to_dict()
# Permutation Importance (on Test)
r = permutation_importance(bin_model, X_te, y_te, n_repeats=5, random_state=42)
bin_perm = {c: float(v) for c, v in zip(feature_cols, r.importances_mean)}

print("==================================================")
print("5. TYPOLOGY MODEL TRAINING (PHASE 7)")
print("==================================================")
train_ill = train_all[train_all["is_illicit"]==1].copy()
test_ill = test_all[test_all["is_illicit"]==1].copy()

le = LabelEncoder()
y_typ_tr = le.fit_transform(train_ill["pattern_type"])
y_typ_te = le.transform(test_ill["pattern_type"])
X_typ_tr = train_ill[feature_cols].values
X_typ_te = test_ill[feature_cols].values

sample_weights = np.array([len(train_ill) / (len(le.classes_) * train_ill["pattern_type"].value_counts()[le.inverse_transform([y])[0]]) for y in y_typ_tr])

typ_model = XGBClassifier(
    n_estimators=500, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    num_class=len(le.classes_), objective="multi:softprob",
    eval_metric="mlogloss", tree_method="hist", random_state=42, verbosity=0
)
typ_model.fit(X_typ_tr, y_typ_tr, sample_weight=sample_weights)
typ_model.save_model(MDLS / "typology_model_v7_candidate.xgb")

y_typ_pred = typ_model.predict(X_typ_te)
y_typ_prob = typ_model.predict_proba(X_typ_te)
typ_metrics = {
    "macro_f1": f1_score(y_typ_te, y_typ_pred, average="macro"),
    "weighted_f1": f1_score(y_typ_te, y_typ_pred, average="weighted"),
    "accuracy": accuracy_score(y_typ_te, y_typ_pred),
}
print(typ_metrics)

typ_gain = pd.Series(typ_model.feature_importances_, index=feature_cols).to_dict()
r_typ = permutation_importance(typ_model, X_typ_te, y_typ_te, n_repeats=5, random_state=42)
typ_perm = {c: float(v) for c, v in zip(feature_cols, r_typ.importances_mean)}

print("==================================================")
print("6. ROBUSTNESS ABLATIONS (PHASE 6 & 8)")
print("==================================================")
amount_feats = ['total_input_mean', 'total_output_mean', 'fee_ratio_mean', 'fee_ratio_std', 'amount_decay_slope', 'output_amount_gini', 'denomination_entropy', 'round_number_ratio', 'io_amount_similarity']
structural_feats = ['num_txns', 'mean_num_inputs', 'mean_num_outputs', 'io_count_ratio', 'unique_input_addrs', 'unique_output_addrs', 'address_reuse_ratio', 'change_output_ratio']
temporal_feats = ['time_span_hours', 'inter_tx_delta_mean', 'inter_tx_delta_std', 'inter_tx_delta_min', 'burstiness_B', 'hour_of_day_entropy', 'prop_delta_mean', 'prop_delta_std', 'prop_delta_cv']
network_feats = ['suspicious_infra_ratio', 'unique_asn_count', 'asn_concentration', 'unique_country_count', 'country_concentration', 'unique_ip_count', 'ip_to_addr_ratio', 'alt_port_ratio', 'unique_user_agents']
script_feats = ['script_type_entropy', 'script_type_mode']
graph_feats = [c for c in feature_cols if c not in amount_feats+structural_feats+temporal_feats+network_feats+script_feats]

ablation_res = {"binary": {}, "typology": {}}
groups = {
    "full": feature_cols,
    "amount": amount_feats, "temporal": temporal_feats, "network": network_feats, "structural": structural_feats, "graph": graph_feats,
    "no_structural": [c for c in feature_cols if c not in structural_feats],
    "no_graph": [c for c in feature_cols if c not in graph_feats]
}
for grp, cols in groups.items():
    c_idx = [feature_cols.index(c) for c in cols if c in feature_cols]
    if not c_idx: continue
    # Binary
    m_b = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
    m_b.fit(X_tr[:, c_idx], y_tr)
    ablation_res["binary"][grp] = roc_auc_score(y_te, m_b.predict_proba(X_te[:, c_idx])[:,1])
    
    # Typology
    m_t = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
    m_t.fit(X_typ_tr[:, c_idx], y_typ_tr)
    ablation_res["typology"][grp] = f1_score(y_typ_te, m_t.predict(X_typ_te[:, c_idx]), average="macro")

print("==================================================")
print("7. CALIBRATION (PHASE 11)")
print("==================================================")
cal_res = {
    "ece": ece_score(y_te, y_te_prob),
    "brier": brier_score_loss(y_te, y_te_prob)
}
print(cal_res)

print("==================================================")
print("8. ERROR ANALYSIS (PHASE 10)")
print("==================================================")
fp_idx = np.where((y_te == 0) & (y_te_pred == 1))[0]
fn_idx = np.where((y_te == 1) & (y_te_pred == 0))[0]
typ_err_idx = np.where(y_typ_te != y_typ_pred)[0]

error_res = {
    "binary_fp": [test_all.iloc[i]["scenario_id"] for i in fp_idx[:5]],
    "binary_fn": [test_all.iloc[i]["scenario_id"] for i in fn_idx[:5]],
    "typology_errs": [test_ill.iloc[i]["scenario_id"] for i in typ_err_idx[:5]]
}

print("==================================================")
print("9. MANIFEST (PHASE 12)")
print("==================================================")
manifest = {
    "dataset_version": "v7_candidate",
    "feature_pipeline_version": "v7_production",
    "train_scenarios": len(train_all),
    "test_scenarios": len(test_all),
    "feature_count": len(feature_cols),
    "feature_names": feature_cols,
    "binary_model": "binary_model_v7_candidate.xgb",
    "typology_model": "typology_model_v7_candidate.xgb",
    "random_seed": 42,
    "evaluation_metrics": {
        "binary": bin_metrics,
        "typology": typ_metrics
    },
    "calibration": cal_res,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

with open(MANS / "MANIFEST_v7_candidate.json", "w") as f:
    json.dump(manifest, f, indent=2)

with open(REPS / "binary_metrics_v7_candidate.json", "w") as f:
    json.dump({"metrics": bin_metrics, "calibration": cal_res}, f, indent=2)
with open(REPS / "typology_metrics_v7_candidate.json", "w") as f:
    json.dump(typ_metrics, f, indent=2)
with open(REPS / "feature_importance_v7_candidate.json", "w") as f:
    json.dump({"binary_gain": bin_gain, "binary_perm": bin_perm, "typology_gain": typ_gain, "typology_perm": typ_perm}, f, indent=2)
with open(REPS / "ablation_v7_candidate.json", "w") as f:
    json.dump(ablation_res, f, indent=2)
with open(REPS / "error_analysis_v7_candidate.json", "w") as f:
    json.dump(error_res, f, indent=2)

print("PIPELINE COMPLETED SUCCESSFULLY")
