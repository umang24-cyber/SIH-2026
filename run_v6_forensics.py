import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, balanced_accuracy_score, f1_score, confusion_matrix, precision_score, recall_score, accuracy_score, average_precision_score, classification_report
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

DATA = "/home/param/SIH-2026/data/processed"

print("==================================================")
print("PART 1 — VERIFY DATA / SPLIT INTEGRITY")
print("==================================================")
feats_train = pd.read_csv(f"{DATA}/scenario_features_train.csv")
feats_test  = pd.read_csv(f"{DATA}/scenario_features_test.csv")
lbls_train  = pd.read_csv(f"{DATA}/scenario_labels_train.csv")
lbls_test   = pd.read_csv(f"{DATA}/scenario_labels_test.csv")

train = feats_train.merge(lbls_train, on="scenario_id")
test  = feats_test.merge(lbls_test, on="scenario_id")

train_scenarios = set(train["scenario_id"])
test_scenarios = set(test["scenario_id"])
intersect_scenarios = train_scenarios.intersection(test_scenarios)
print(f"Train scenarios: {len(train_scenarios)}")
print(f"Test scenarios: {len(test_scenarios)}")
print(f"Scenario intersection: {len(intersect_scenarios)}")

# Feature families
amount_feats = ['total_input_mean', 'total_output_mean', 'fee_ratio_mean', 'fee_ratio_std', 'amount_decay_slope', 'output_amount_gini', 'denomination_entropy', 'round_number_ratio', 'io_amount_similarity']
structural_feats = ['num_txns', 'mean_num_inputs', 'mean_num_outputs', 'io_count_ratio', 'unique_input_addrs', 'unique_output_addrs', 'address_reuse_ratio', 'change_output_ratio']
temporal_feats = ['time_span_hours', 'inter_tx_delta_mean', 'inter_tx_delta_std', 'inter_tx_delta_min', 'burstiness_B', 'hour_of_day_entropy', 'prop_delta_mean', 'prop_delta_std', 'prop_delta_cv']
network_feats = ['suspicious_infra_ratio', 'unique_asn_count', 'asn_concentration', 'unique_country_count', 'country_concentration', 'unique_ip_count', 'ip_to_addr_ratio', 'alt_port_ratio', 'unique_user_agents']
script_feats = ['script_type_entropy', 'script_type_mode']

try:
    graph_train = pd.read_csv(f"{DATA}/scenario_graph_features_train.csv")
    graph_test = pd.read_csv(f"{DATA}/scenario_graph_features_test.csv")
    graph_feats = [c for c in graph_train.columns if c != "scenario_id"]
    train = train.merge(graph_train, on="scenario_id")
    test = test.merge(graph_test, on="scenario_id")
except:
    graph_feats = []

feature_cols = amount_feats + structural_feats + temporal_feats + network_feats + script_feats + graph_feats
X_train = train[feature_cols].fillna(0)
y_train = train["is_illicit"]
X_test = test[feature_cols].fillna(0)
y_test = test["is_illicit"]

print("\n==================================================")
print("PART 3 — SINGLE FEATURE BINARY AUDIT")
print("==================================================")
single_aucs = {}
for col in feature_cols:
    auc = roc_auc_score(y_test, X_test[col])
    if auc < 0.5:
        auc = 1.0 - auc
    single_aucs[col] = auc
for col, auc in sorted(single_aucs.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"{col}: {auc:.4f}")

print("\n==================================================")
print("PART 4 — SIMPLE BINARY CLASSIFIER AUDIT")
print("==================================================")
for depth in [1, 2, 3]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_train, y_train)
    preds = dt.predict(X_test)
    probs = dt.predict_proba(X_test)[:, 1]
    bacc = balanced_accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)
    print(f"Depth-{depth} DT: AUC={auc:.4f}, BAcc={bacc:.4f}")

lr = LogisticRegression(max_iter=1000, random_state=42)
sc = StandardScaler()
lr.fit(sc.fit_transform(X_train), y_train)
preds = lr.predict(sc.transform(X_test))
probs = lr.predict_proba(sc.transform(X_test)[:, :])[:, 1]
print(f"Logistic Regression: AUC={roc_auc_score(y_test, probs):.4f}, BAcc={balanced_accuracy_score(y_test, preds):.4f}")

print("\n==================================================")
print("PART 5 — FULL XGBOOST BINARY VALIDATION")
print("==================================================")
xgb = XGBClassifier(n_estimators=200, max_depth=6, random_state=42, tree_method="hist")
xgb.fit(X_train, y_train)
preds = xgb.predict(X_test)
probs = xgb.predict_proba(X_test)[:, 1]
print(f"XGBoost ROC AUC: {roc_auc_score(y_test, probs):.4f}")
print(f"XGBoost PR AUC: {average_precision_score(y_test, probs):.4f}")
print(f"XGBoost F1: {f1_score(y_test, preds):.4f}")
print(f"XGBoost BAcc: {balanced_accuracy_score(y_test, preds):.4f}")

print("\n==================================================")
print("PART 6 — FEATURE GROUP ABLATION (BINARY)")
print("==================================================")
groups = {
    "Amount": amount_feats, "Temporal": temporal_feats, "Structural": structural_feats,
    "Network": network_feats, "Graph": graph_feats, "Script": script_feats, "All": feature_cols
}
for gname, gcols in groups.items():
    if not gcols: continue
    model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
    model.fit(X_train[gcols], y_train)
    p = model.predict(X_test[gcols])
    pr = model.predict_proba(X_test[gcols])[:, 1]
    print(f"{gname}: AUC={roc_auc_score(y_test, pr):.4f}, BAcc={balanced_accuracy_score(y_test, p):.4f}")

print("\n==================================================")
print("PART 7 — TYPOLOGY VALIDATION")
print("==================================================")
illicit_train = train[train["is_illicit"] == 1]
illicit_test = test[test["is_illicit"] == 1]
le = LabelEncoder()
y_typ_train = le.fit_transform(illicit_train["pattern_type"])
y_typ_test = le.transform(illicit_test["pattern_type"])
X_typ_train = illicit_train[feature_cols].fillna(0)
X_typ_test = illicit_test[feature_cols].fillna(0)

xgb_typ = XGBClassifier(n_estimators=200, max_depth=6, random_state=42, tree_method="hist")
xgb_typ.fit(X_typ_train, y_typ_train)
preds_typ = xgb_typ.predict(X_typ_test)
probs_typ = xgb_typ.predict_proba(X_typ_test)
print(f"Macro-F1: {f1_score(y_typ_test, preds_typ, average='macro'):.4f}")
print("Per-class F1:")
for i, cls in enumerate(le.classes_):
    print(f"  {cls}: {f1_score((y_typ_test == i), (preds_typ == i)):.4f}")

print("\n==================================================")
print("PART 8 — TYPOLOGY FEATURE-GROUP ABLATION")
print("==================================================")
for gname, gcols in groups.items():
    if not gcols: continue
    model = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
    model.fit(X_typ_train[gcols], y_typ_train)
    p = model.predict(X_typ_test[gcols])
    print(f"{gname}: Macro-F1={f1_score(y_typ_test, p, average='macro'):.4f}")

