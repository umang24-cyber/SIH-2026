import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score

features = pd.read_csv("data/processed/scenario_features_full_test.csv")
labels = pd.read_csv("data/processed/scenario_labels_test.csv")

merged = features.merge(labels, on="scenario_id")
X = merged.drop(columns=["is_illicit", "pattern_type", "scenario_id", "split", "is_licit_exchange"], errors="ignore").values
y = merged["is_illicit"].values

model = xgb.XGBClassifier()
model.load_model("ml/models/binary_model_v7_candidate.ubj")
y_prob = model.predict_proba(X)[:,1]

print("V7 on V7 AUC:", roc_auc_score(y, y_prob))
