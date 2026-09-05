import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import f1_score, roc_auc_score, pairwise_distances
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.inspection import permutation_importance
import warnings
warnings.filterwarnings('ignore')

DATA = "/home/param/SIH-2026/data/processed"

feats_train = pd.read_csv(f"{DATA}/scenario_features_train.csv")
feats_test  = pd.read_csv(f"{DATA}/scenario_features_test.csv")
lbls_train  = pd.read_csv(f"{DATA}/scenario_labels_train.csv")
lbls_test   = pd.read_csv(f"{DATA}/scenario_labels_test.csv")
graph_train = pd.read_csv(f"{DATA}/scenario_graph_features_train.csv")
graph_test = pd.read_csv(f"{DATA}/scenario_graph_features_test.csv")

train = feats_train.merge(lbls_train, on="scenario_id").merge(graph_train, on="scenario_id")
test  = feats_test.merge(lbls_test, on="scenario_id").merge(graph_test, on="scenario_id")

illicit_train = train[train["is_illicit"] == 1]
illicit_test = test[test["is_illicit"] == 1]

le = LabelEncoder()
y_train = le.fit_transform(illicit_train["pattern_type"])
y_test = le.transform(illicit_test["pattern_type"])
classes = le.classes_

amount_feats = ['total_input_mean', 'total_output_mean', 'fee_ratio_mean', 'fee_ratio_std', 'amount_decay_slope', 'output_amount_gini', 'denomination_entropy', 'round_number_ratio', 'io_amount_similarity']
structural_feats = ['num_txns', 'mean_num_inputs', 'mean_num_outputs', 'io_count_ratio', 'unique_input_addrs', 'unique_output_addrs', 'address_reuse_ratio', 'change_output_ratio']
temporal_feats = ['time_span_hours', 'inter_tx_delta_mean', 'inter_tx_delta_std', 'inter_tx_delta_min', 'burstiness_B', 'hour_of_day_entropy', 'prop_delta_mean', 'prop_delta_std', 'prop_delta_cv']
network_feats = ['suspicious_infra_ratio', 'unique_asn_count', 'asn_concentration', 'unique_country_count', 'country_concentration', 'unique_ip_count', 'ip_to_addr_ratio', 'alt_port_ratio', 'unique_user_agents']
script_feats = ['script_type_entropy', 'script_type_mode']
graph_feats = [c for c in graph_train.columns if c != "scenario_id"]

all_struct = structural_feats + graph_feats
X_train = illicit_train[all_struct].fillna(0)
X_test = illicit_test[all_struct].fillna(0)
all_X_train = illicit_train[amount_feats + structural_feats + temporal_feats + network_feats + script_feats + graph_feats].fillna(0)
all_X_test = illicit_test[amount_feats + structural_feats + temporal_feats + network_feats + script_feats + graph_feats].fillna(0)


print("==================================================")
print("2. STRUCTURAL FEATURE STATISTICS (TEST SET)")
print("==================================================")
for feat in all_struct:
    print(f"\n--- {feat} ---")
    for i, c in enumerate(classes):
        vals = X_test[y_test == i][feat]
        print(f"  {c:<15}: mean={vals.mean():.4f}, std={vals.std():.4f}, min={vals.min():.4f}, max={vals.max():.4f}")

print("\n==================================================")
print("3. ACTUAL PERFECT-SEPARATION RULES (SHALLOW TREES)")
print("==================================================")
for d in [1, 2, 3, 4]:
    dt = DecisionTreeClassifier(max_depth=d, random_state=42)
    dt.fit(X_train, y_train)
    p = dt.predict(X_test)
    print(f"\nDepth-{d} Tree Macro-F1: {f1_score(y_test, p, average='macro'):.4f}")
    if d <= 3:
        print(export_text(dt, feature_names=list(X_train.columns)))

print("\n==================================================")
print("4. SINGLE-FEATURE TYPOLOGY AUDIT")
print("==================================================")
from sklearn.metrics import roc_auc_score
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for feat in all_struct:
        dt = DecisionTreeClassifier(max_depth=4, random_state=42)
        dt.fit(X_train[[feat]], y_train)
        p = dt.predict(X_test[[feat]])
        f1 = f1_score(y_test, p, average='macro')
        
        # OvR AUC
        aucs = []
        for i, c in enumerate(classes):
            y_tr_b = (y_train == i).astype(int)
            y_ts_b = (y_test == i).astype(int)
            if y_ts_b.sum() == 0: continue
            try:
                lr = LogisticRegression(random_state=42).fit(X_train[[feat]], y_tr_b)
                probs = lr.predict_proba(X_test[[feat]])[:, 1]
                aucs.append(roc_auc_score(y_ts_b, probs))
            except:
                pass
        mean_auc = np.mean(aucs) if aucs else 0
        print(f"{feat:<25} : Macro-F1 = {f1:.4f}, Mean OvR AUC = {mean_auc:.4f}")

print("\n==================================================")
print("5. DISTRIBUTION OVERLAP (WASSERSTEIN)")
print("==================================================")
from scipy.stats import wasserstein_distance
# Compare Ransomware to others for max_in_degree
for feat in ["max_in_degree", "max_chain_length", "edge_to_node_ratio", "degree_assortativity"]:
    print(f"\n{feat}:")
    for i in range(len(classes)):
        for j in range(i+1, len(classes)):
            v1 = X_test[y_test == i][feat]
            v2 = X_test[y_test == j][feat]
            # Normalize to 0-1 for meaningful W-distance
            mmin, mmax = min(v1.min(), v2.min()), max(v1.max(), v2.max())
            if mmax > mmin:
                v1_n = (v1 - mmin) / (mmax - mmin)
                v2_n = (v2 - mmin) / (mmax - mmin)
                wd = wasserstein_distance(v1_n, v2_n)
            else:
                wd = 0
            print(f"  {classes[i]} vs {classes[j]}: W-Dist={wd:.4f}")

print("\n==================================================")
print("10. MORPHOLOGY-REMOVAL ABLATIONS")
print("==================================================")
degree = ["max_in_degree", "max_out_degree", "mean_num_inputs", "mean_num_outputs"]
chain = ["max_chain_length", "branching_factor_mean"]
fan = ["unique_input_addrs", "unique_output_addrs"]
reuse = ["address_reuse_ratio"]
density = ["edge_to_node_ratio", "io_count_ratio"]

abls = {
    "A. No Degree": [c for c in all_X_train.columns if c not in degree],
    "B. No Chain": [c for c in all_X_train.columns if c not in chain],
    "C. No Fan": [c for c in all_X_train.columns if c not in fan],
    "D. No Reuse": [c for c in all_X_train.columns if c not in reuse],
    "E. No Density": [c for c in all_X_train.columns if c not in density],
    "F. No Graph": [c for c in all_X_train.columns if c not in graph_feats],
    "G. No Structural": [c for c in all_X_train.columns if c not in all_struct]
}

for name, cols in abls.items():
    xgb = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
    xgb.fit(all_X_train[cols], y_train)
    p = xgb.predict(all_X_test[cols])
    print(f"{name}: Macro-F1 = {f1_score(y_test, p, average='macro'):.4f}")


print("\n==================================================")
print("11. PERMUTATION IMPORTANCE")
print("==================================================")
xgb_full = XGBClassifier(n_estimators=100, max_depth=4, random_state=42, tree_method="hist")
xgb_full.fit(all_X_train, y_train)
r = permutation_importance(xgb_full, all_X_test, y_test, n_repeats=5, random_state=42)
imp = sorted([(c, r.importances_mean[i]) for i, c in enumerate(all_X_train.columns)], key=lambda x: x[1], reverse=True)
for c, val in imp[:15]:
    print(f"{c:<25}: {val:.4f}")

grps = {
    "Amount": amount_feats, "Temporal": temporal_feats, "Structural": structural_feats,
    "Network": network_feats, "Graph": graph_feats, "Script": script_feats
}
for gname, gcols in grps.items():
    idx = [all_X_train.columns.get_loc(c) for c in gcols if c in all_X_train.columns]
    val = sum(r.importances_mean[i] for i in idx)
    print(f"GROUP {gname:<15}: {val:.4f}")
