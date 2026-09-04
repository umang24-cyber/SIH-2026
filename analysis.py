import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
import json

DATA = "/home/param/SIH-2026/data/processed"

feats_train = pd.read_csv(f"{DATA}/scenario_features_full_train.csv")
feats_test  = pd.read_csv(f"{DATA}/scenario_features_full_test.csv")
lbls_train  = pd.read_csv(f"{DATA}/scenario_labels_train.csv")
lbls_test   = pd.read_csv(f"{DATA}/scenario_labels_test.csv")

train = feats_train.merge(lbls_train, on="scenario_id")
test  = feats_test.merge(lbls_test, on="scenario_id")
all_data = pd.concat([train, test], ignore_index=True)

feature_cols = [c for c in feats_train.columns if c not in ["scenario_id", "is_illicit", "pattern_type"]]

print("="*60)
print("1. GATE B: Exact 2 features and thresholds")
print("="*60)
X_all = all_data[feature_cols].fillna(0).values.astype(float)
y_all = all_data["is_illicit"].values

dt = DecisionTreeClassifier(max_depth=2, random_state=42)
dt.fit(X_all, y_all)
tree_rules = export_text(dt, feature_names=feature_cols)
print(tree_rules)

print("="*60)
print("3. GATE I: Top 3 ablation and replacement")
print("="*60)
illicit_train = train[train["is_illicit"] == 1].copy()
illicit_test = test[test["is_illicit"] == 1].copy()

le = LabelEncoder()
le.fit(illicit_train["pattern_type"])
y_typ_train = le.transform(illicit_train["pattern_type"])
y_typ_test = le.transform(illicit_test["pattern_type"])

X_typ_train = illicit_train[feature_cols].fillna(0).copy()
X_typ_test = illicit_test[feature_cols].fillna(0).copy()

classes = le.classes_

for i, cls in enumerate(classes):
    print(f"\n--- {cls} ---")
    y_bin = (y_typ_train == i).astype(int)
    
    # Baseline
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", random_state=42, verbosity=0
    )
    model.fit(X_typ_train, y_bin)
    
    importances = pd.Series(model.feature_importances_, index=feature_cols)
    top3 = importances.nlargest(3).index.tolist()
    print(f"Original top 3: {top3}")
    
    # Ablated
    ablated_cols = [c for c in feature_cols if c not in top3]
    model_abl = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        tree_method="hist", random_state=42, verbosity=0
    )
    model_abl.fit(X_typ_train[ablated_cols], y_bin)
    
    importances_abl = pd.Series(model_abl.feature_importances_, index=ablated_cols)
    top3_repl = importances_abl.nlargest(3).index.tolist()
    print(f"Replacement top 3: {top3_repl}")
    
    for orig in top3:
        for repl in top3_repl:
            corr = all_data[orig].corr(all_data[repl])
            print(f"Corr {orig} <-> {repl}: {corr:.4f}")

print("="*60)
print("4. CORRELATED STRUCTURAL CLUSTER")
print("="*60)
cluster_cols = ["mean_num_inputs", "fanin_ratio", "address_reuse_ratio", "edge_to_node_ratio", "unique_input_addrs", "max_chain_length"]
corr_matrix = all_data[cluster_cols].corr()
print(corr_matrix.to_string())

