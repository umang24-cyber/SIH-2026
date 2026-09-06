"""
04_train_typology.py — Stage 2 typology classifier (illicit-only, 4-class).
Run from SIH-2026/:
    conda activate ml && python ml/04_train_typology.py
"""
import json, pickle, warnings
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
OUT  = ROOT / "ml" / "outputs"
MDLS = ROOT / "ml" / "models"
OUT.mkdir(parents=True, exist_ok=True); MDLS.mkdir(parents=True, exist_ok=True)

FORBIDDEN = {"scenario_id","is_illicit","pattern_type","is_licit_exchange","split"}
TYPOLOGIES = ["ransomware","peeling_chain","layering","mixing"]

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

# ---------------------------------------------------------------------------
sep("1. LOADING DATA")
feats_tr = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_te = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_tr  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_te  = pd.read_csv(DATA / "scenario_labels_test.csv")

train_all = feats_tr.merge(lbls_tr, on="scenario_id")
test_all  = feats_te.merge(lbls_te, on="scenario_id")

# Filter to illicit only
train = train_all[train_all["is_illicit"]==1].copy()
test  = test_all[ test_all["is_illicit"]==1].copy()
print(f"  Train illicit scenarios: {len(train):,}")
print(f"  Test  illicit scenarios: {len(test):,}")
print("\n  Train typology counts:")
print(train["pattern_type"].value_counts().to_string())
print("\n  Test typology counts:")
print(test["pattern_type"].value_counts().to_string())

feature_cols = [c for c in feats_tr.columns if c not in FORBIDDEN]

# Encode labels
le = LabelEncoder()
le.fit(TYPOLOGIES)
y_tr = le.transform(train["pattern_type"])
y_te = le.transform(test["pattern_type"])
print(f"\n  Label encoding: {dict(zip(le.classes_, le.transform(le.classes_)))}")

X_tr = train[feature_cols].values
X_te = test[feature_cols].values
groups_tr = train["scenario_id"].values  # for grouped CV

# ---------------------------------------------------------------------------
sep("2. TYPOLOGY DISTRIBUTION PRE-CHECK")
print("  Checking if trivial rules can separate typologies...")
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import balanced_accuracy_score

check_feats = ["time_span_hours","num_txns","unique_ip_count",
               "fanout_ratio","fanin_ratio","max_chain_length",
               "inter_tx_delta_mean","burstiness_B","graph_density"]
for feat in check_feats:
    if feat not in feature_cols: continue
    idx = feature_cols.index(feat)
    dt = DecisionTreeClassifier(max_depth=2, random_state=42)
    dt.fit(X_tr[:,idx:idx+1], y_tr)
    ba = balanced_accuracy_score(y_te, dt.predict(X_te[:,idx:idx+1]))
    random_ba = 1.0 / len(TYPOLOGIES)
    print(f"  {feat:<35} depth-2 tree balanced_acc={ba:.4f}  (random={random_ba:.4f})")

# ---------------------------------------------------------------------------
sep("3. CLASS WEIGHTS")
class_counts = train["pattern_type"].value_counts()
n_total = len(train)
sample_weights = np.array([n_total / (len(TYPOLOGIES) * class_counts[le.inverse_transform([y])[0]])
                            for y in y_tr])
print(f"  Class sample weights (min/max): {sample_weights.min():.3f} / {sample_weights.max():.3f}")
print("  Per-class counts:", class_counts.to_dict())

# ---------------------------------------------------------------------------
sep("4. GROUPED K-FOLD CV (scenario-level, k=5)")
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1_scores = []
for fold, (idx_tr, idx_va) in enumerate(sgkf.split(X_tr, y_tr, groups=groups_tr)):
    Xf_tr, yf_tr = X_tr[idx_tr], y_tr[idx_tr]
    Xf_va, yf_va = X_tr[idx_va], y_tr[idx_va]
    sw_tr = sample_weights[idx_tr]
    # Verify no scenario leakage
    grp_tr_set = set(groups_tr[idx_tr]); grp_va_set = set(groups_tr[idx_va])
    assert len(grp_tr_set & grp_va_set) == 0, "Scenario leakage in CV!"
    m = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                      subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
                      num_class=len(TYPOLOGIES), objective="multi:softprob",
                      eval_metric="mlogloss", tree_method="hist",
                      random_state=42, verbosity=0)
    m.fit(Xf_tr, yf_tr, sample_weight=sw_tr)
    preds = m.predict(Xf_va)
    f1 = f1_score(yf_va, preds, average="macro")
    cv_f1_scores.append(f1)
    print(f"  Fold {fold+1}: macro-F1 = {f1:.4f}")
print(f"\n  CV macro-F1: {np.mean(cv_f1_scores):.4f} ± {np.std(cv_f1_scores):.4f}")

# ---------------------------------------------------------------------------
sep("5. FINAL TYPOLOGY MODEL TRAINING")
model_typ = XGBClassifier(
    n_estimators=500, max_depth=5, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    num_class=len(TYPOLOGIES), objective="multi:softprob",
    eval_metric="mlogloss", tree_method="hist",
    random_state=42, verbosity=0,
)
model_typ.fit(X_tr, y_tr, sample_weight=sample_weights)
print("  Training complete.")

# ---------------------------------------------------------------------------
sep("6. TEST SET EVALUATION")
y_pred = model_typ.predict(X_te)
macro_f1 = f1_score(y_te, y_pred, average="macro")
print(f"\n  Macro-F1: {macro_f1:.4f}")
print("\n  Classification Report:")
print(classification_report(y_te, y_pred, target_names=le.classes_,
                             labels=list(range(len(le.classes_)))))

cm = confusion_matrix(y_te, y_pred)
print(f"\n  Confusion matrix (rows=true, cols=pred):")
cm_df = pd.DataFrame(cm, index=le.classes_, columns=[f"pred_{c}" for c in le.classes_])
print(cm_df.to_string())

# Per-class F1
cr = classification_report(y_te, y_pred, target_names=le.classes_,
                            labels=list(range(len(le.classes_))),
                            output_dict=True)

# ---------------------------------------------------------------------------
sep("7. FEATURE IMPORTANCE")
imp = pd.Series(model_typ.feature_importances_, index=feature_cols).sort_values(ascending=False)
print("  Top-20 features (gain):")
print(imp.head(20).to_string())

# Feature importance plot
fig, ax = plt.subplots(figsize=(10,7))
top20 = imp.head(20)
ax.barh(top20.index[::-1], top20.values[::-1], color="#6B8CDE", alpha=0.85)
ax.set_xlabel("Feature Importance (Gain)"); ax.set_title("Top-20 Feature Importances — Typology Model", fontweight="bold")
plt.tight_layout(); fig.savefig(OUT/"typology_feature_importance_v3.png", dpi=150); plt.close()
print(f"  Saved: {OUT/'typology_feature_importance_v3.png'}")

# Confusion matrix plot
fig, ax = plt.subplots(figsize=(7,6))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(len(le.classes_))); ax.set_yticks(range(len(le.classes_)))
ax.set_xticklabels([f"Pred\n{c}" for c in le.classes_], fontsize=8)
ax.set_yticklabels(le.classes_, fontsize=8)
for i in range(len(le.classes_)):
    for j in range(len(le.classes_)):
        ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                color="white" if cm[i,j] > cm.max()/2 else "black", fontsize=11)
ax.set_title("Confusion Matrix — Typology Classifier (v3)", fontweight="bold")
plt.colorbar(im, ax=ax); plt.tight_layout()
fig.savefig(OUT/"typology_confusion_matrix_v3.png", dpi=150); plt.close()
print(f"  Saved: {OUT/'typology_confusion_matrix_v3.png'}")

# ---------------------------------------------------------------------------
sep("8. SAVE MODEL + METRICS")
model_typ.save_model(str(MDLS/"typology_xgb_v1.json"))
with open(MDLS/"typology_label_encoder.json","w") as f:
    json.dump({"classes": list(le.classes_)}, f)
print(f"  Saved: {MDLS/'typology_xgb_v1.json'}")

# Write metrics markdown
lines = ["# Typology Model Metrics — v3\n",
         f"\n**CV Macro-F1:** {np.mean(cv_f1_scores):.4f} ± {np.std(cv_f1_scores):.4f}",
         f"\n**Test Macro-F1:** {macro_f1:.4f}\n",
         "\n## Per-Class Results\n",
         "| Class | Precision | Recall | F1 | Support |",
         "|---|---|---|---|---|"]
for cls in le.classes_:
    r = cr[cls]
    lines.append(f"| {cls} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1-score']:.4f} | {int(r['support'])} |")
lines.append(f"\n## Confusion Matrix\n\n{cm_df.to_markdown()}")
(OUT/"typology_metrics_v3.md").write_text("\n".join(lines))
print(f"  Saved: {OUT/'typology_metrics_v3.md'}")

sep("DONE — 04_train_typology.py")
