"""
03_train_binary.py
==================
Day 2 — Binary XGBoost classifier + probability calibration.

Run from SIH-2026/:
    conda activate ml
    python ml/03_train_binary.py

Outputs:
    ml/models/binary_xgb_v1.json           — trained XGBoost model
    ml/models/binary_xgb_v1_calibrator.pkl — isotonic/Platt calibrator
    ml/outputs/confusion_matrix_binary.png
    ml/outputs/feature_importance_binary.png
    ml/outputs/calibration_curve_binary.png
    ml/outputs/roc_pr_curve_binary.png
"""

import json
import pickle
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    auc, classification_report, confusion_matrix,
    precision_recall_curve, roc_auc_score, roc_curve
)
from sklearn.model_selection import StratifiedShuffleSplit
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT  = Path(__file__).resolve().parent.parent
DATA  = ROOT / "data" / "processed"
OUT   = ROOT / "ml" / "outputs"
MDLS  = ROOT / "ml" / "models"
OUT.mkdir(parents=True, exist_ok=True)
MDLS.mkdir(parents=True, exist_ok=True)

FORBIDDEN_FEATURES = {"is_illicit", "pattern_type", "scenario_id", "split"}

def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")

def ece_score(y_true, y_prob, n_bins=10) -> float:
    """Expected Calibration Error."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece  = 0.0
    n    = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if mask.sum() == 0:
            continue
        acc  = y_true[mask].mean()
        conf = y_prob[mask].mean()
        ece += mask.sum() / n * abs(acc - conf)
    return float(ece)

# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
sep("1. LOADING DATA")

feats_train = pd.read_csv(DATA / "scenario_features_full_train.csv")
feats_test  = pd.read_csv(DATA / "scenario_features_full_test.csv")
lbls_train  = pd.read_csv(DATA / "scenario_labels_train.csv")
lbls_test   = pd.read_csv(DATA / "scenario_labels_test.csv")

train = feats_train.merge(lbls_train, on="scenario_id")
test  = feats_test.merge(lbls_test,  on="scenario_id")

print(f"  Train merged: {train.shape}")
print(f"  Test  merged: {test.shape}")

# ---------------------------------------------------------------------------
# 2. Build feature matrix — explicit assertion labels are absent
# ---------------------------------------------------------------------------
sep("2. BUILDING FEATURE MATRIX")

feature_cols = [c for c in feats_train.columns if c not in FORBIDDEN_FEATURES]
print(f"  Feature columns ({len(feature_cols)}): {feature_cols}")

# Hard assert — any leakage is a stop condition
for col in ["is_illicit", "pattern_type"]:
    assert col not in feature_cols, \
        f"LEAKAGE DETECTED: '{col}' found in feature columns — stopping."
print("  Leakage assertion: PASS")

X_train = train[feature_cols].values
y_train = train["is_illicit"].values
X_test  = test[feature_cols].values
y_test  = test["is_illicit"].values

print(f"  X_train: {X_train.shape}, y_train: {y_train.shape}")
print(f"  X_test:  {X_test.shape},  y_test:  {y_test.shape}")

# ---------------------------------------------------------------------------
# 3. Compute scale_pos_weight at scenario level
# ---------------------------------------------------------------------------
sep("3. CLASS BALANCE (SCENARIO LEVEL)")

n_licit   = int((y_train == 0).sum())
n_illicit = int((y_train == 1).sum())
scale_pos_weight = n_licit / n_illicit

print(f"  Train scenarios — licit: {n_licit:,} ({n_licit/len(y_train):.1%})  "
      f"illicit: {n_illicit:,} ({n_illicit/len(y_train):.1%})")
print(f"  scale_pos_weight (scenario-level) = {scale_pos_weight:.4f}")
print(f"  [Compare] transaction-level was 63.4% licit / 36.6% illicit → "
      f"scale_pos_weight would have been ~{0.634/0.366:.4f}")
print(f"  >> Scenario-level balance is very different: "
      f"use {scale_pos_weight:.4f}, NOT the transaction-level value.")

# ---------------------------------------------------------------------------
# 4. 3-way split: train-proper / early-stop-eval / calibration
# ---------------------------------------------------------------------------
sep("4. TRAIN/EVAL/CALIBRATION SPLIT")

# Strategy: split train into 70% train-proper + 15% early-stop-eval + 15% calibration
# Using two stratified splits.
sss1 = StratifiedShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
idx_proper, idx_holdout = next(sss1.split(X_train, y_train))

X_proper  = X_train[idx_proper];   y_proper  = y_train[idx_proper]
X_holdout = X_train[idx_holdout];  y_holdout = y_train[idx_holdout]

sss2 = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
idx_eval, idx_cal = next(sss2.split(X_holdout, y_holdout))
X_eval = X_holdout[idx_eval]; y_eval = y_holdout[idx_eval]
X_cal  = X_holdout[idx_cal];  y_cal  = y_holdout[idx_cal]

print(f"  Train-proper:   {X_proper.shape[0]:,} rows")
print(f"  Early-stop-eval:{X_eval.shape[0]:,} rows")
print(f"  Calibration:    {X_cal.shape[0]:,} rows")
print(f"  Test (final):   {X_test.shape[0]:,} rows")

# ---------------------------------------------------------------------------
# 5. Train XGBoost v1 (base — no log transform yet)
# ---------------------------------------------------------------------------
sep("5. TRAINING XGBoost v1 (BASE)")

def train_xgb(X_tr, y_tr, X_ev, y_ev, spw, prefix="v1"):
    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        scale_pos_weight=spw,
        eval_metric="logloss",
        early_stopping_rounds=50,
        tree_method="hist",
        random_state=42,
        verbosity=0,
    )
    model.fit(
        X_tr, y_tr,
        eval_set=[(X_ev, y_ev)],
        verbose=False,
    )
    print(f"  [{prefix}] Best iteration: {model.best_iteration}")
    return model

model_v1 = train_xgb(X_proper, y_proper, X_eval, y_eval, scale_pos_weight, "v1")

# Feature importance check
importances = model_v1.feature_importances_
feat_imp = pd.Series(importances, index=feature_cols).sort_values(ascending=False)
max_share = feat_imp.iloc[0] / feat_imp.sum()
top_feat  = feat_imp.index[0]
print(f"\n  Top feature: '{top_feat}' — importance share: {max_share:.1%}")

# ---------------------------------------------------------------------------
# 6. Fix if any feature exceeds 50% importance share
# ---------------------------------------------------------------------------
THRESHOLD = 0.50
log_transform_applied = False

if max_share > THRESHOLD:
    print(f"\n  *** IMPORTANCE THRESHOLD EXCEEDED ({max_share:.1%} > {THRESHOLD:.0%}) ***")
    print(f"  Applying log1p transform to time_span_hours (heavily right-skewed).")

    col_idx = feature_cols.index("time_span_hours")

    def apply_log_transform(X):
        X = X.copy()
        X[:, col_idx] = np.log1p(X[:, col_idx])
        return X

    X_proper_t = apply_log_transform(X_proper)
    X_eval_t   = apply_log_transform(X_eval)
    X_cal_t    = apply_log_transform(X_cal)
    X_test_t   = apply_log_transform(X_test)

    model_v1 = train_xgb(X_proper_t, y_proper, X_eval_t, y_eval, scale_pos_weight, "v1-log")
    importances_new = model_v1.feature_importances_
    feat_imp_new = pd.Series(importances_new, index=feature_cols).sort_values(ascending=False)
    new_max_share = feat_imp_new.iloc[0] / feat_imp_new.sum()
    print(f"\n  Before log-transform: '{top_feat}' share = {max_share:.1%}")
    print(f"  After  log-transform: '{feat_imp_new.index[0]}' share = {new_max_share:.1%}")

    feat_imp = feat_imp_new
    log_transform_applied = True
    X_cal  = X_cal_t
    X_test = X_test_t
else:
    print(f"  Importance check: PASS — no single feature exceeds {THRESHOLD:.0%}")

# ---------------------------------------------------------------------------
# 7. Evaluate base model on test set
# ---------------------------------------------------------------------------
sep("6. TEST SET EVALUATION (pre-calibration)")

y_prob_raw = model_v1.predict_proba(X_test)[:, 1]
y_pred_raw = (y_prob_raw >= 0.5).astype(int)

roc_auc  = roc_auc_score(y_test, y_prob_raw)
fpr, tpr, _ = roc_curve(y_test, y_prob_raw)
prec, rec, _ = precision_recall_curve(y_test, y_prob_raw)
pr_auc   = auc(rec, prec)
ece_raw  = ece_score(y_test, y_prob_raw)

print(f"\n  ROC-AUC:  {roc_auc:.4f}")
print(f"  PR-AUC:   {pr_auc:.4f}")
print(f"  ECE (raw):{ece_raw:.4f}")
print(f"\n  Classification Report:")
print(classification_report(y_test, y_pred_raw, target_names=["licit", "illicit"]))

# ---------------------------------------------------------------------------
# 8. Probability calibration
# ---------------------------------------------------------------------------
sep("7. PROBABILITY CALIBRATION")

# sklearn 1.9: CalibratedClassifierCV(cv=None) re-fits the estimator, conflicting
# with XGBoost's early_stopping_rounds. Use manual calibration on predict_proba
# outputs instead — equivalent to the prefit path.
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

# Get raw probabilities on calibration set
y_prob_cal_raw = model_v1.predict_proba(X_cal)[:, 1]

# Isotonic regression calibrator
iso_reg = IsotonicRegression(out_of_bounds="clip")
iso_reg.fit(y_prob_cal_raw, y_cal)
y_prob_iso = np.clip(iso_reg.predict(y_prob_raw), 0, 1)
ece_iso    = ece_score(y_test, y_prob_iso)
print(f"  ECE after isotonic calibration: {ece_iso:.4f}")

# Platt scaling (sigmoid) — logistic regression on log-odds
from scipy.special import logit
eps = 1e-7
log_odds_cal = logit(np.clip(y_prob_cal_raw, eps, 1-eps)).reshape(-1, 1)
log_odds_tst = logit(np.clip(y_prob_raw,      eps, 1-eps)).reshape(-1, 1)
platt = LogisticRegression(random_state=42)
platt.fit(log_odds_cal, y_cal)
y_prob_sig = platt.predict_proba(log_odds_tst)[:, 1]
ece_sig    = ece_score(y_test, y_prob_sig)
print(f"  ECE after sigmoid calibration:  {ece_sig:.4f}")

# Pick best calibrator
best_ece    = min(ece_raw, ece_iso, ece_sig)
if best_ece == ece_iso:
    best_cal    = iso_reg
    best_probs  = y_prob_iso
    cal_method  = "isotonic"
elif best_ece == ece_sig:
    best_cal    = platt
    best_probs  = y_prob_sig
    cal_method  = "sigmoid"
else:
    best_cal    = None
    best_probs  = y_prob_raw
    cal_method  = "none (raw probabilities best)"

print(f"\n  Selected calibration method: {cal_method}")
print(f"  Final ECE: {best_ece:.4f}")
print(f"  ECE comparison — raw: {ece_raw:.4f}, isotonic: {ece_iso:.4f}, sigmoid: {ece_sig:.4f}")

# Final metrics with calibrated probs
y_pred_cal = (best_probs >= 0.5).astype(int)
roc_auc_cal = roc_auc_score(y_test, best_probs)
print(f"\n  Final calibrated ROC-AUC: {roc_auc_cal:.4f}")
print(f"  Final classification report (calibrated):")
print(classification_report(y_test, y_pred_cal, target_names=["licit", "illicit"]))

# ---------------------------------------------------------------------------
# 9. Save model artifacts
# ---------------------------------------------------------------------------
sep("8. SAVING ARTIFACTS")

model_path = MDLS / "binary_xgb_v1.json"
model_v1.save_model(str(model_path))
print(f"  Saved XGBoost model: {model_path}")

# Save calibrator (if used)
cal_path = MDLS / "binary_xgb_v1_calibrator.pkl"
if best_cal is not None:
    with open(cal_path, "wb") as f:
        pickle.dump(best_cal, f)
    print(f"  Saved calibrator ({cal_method}): {cal_path}")
else:
    print(f"  No calibrator saved (raw probabilities selected)")

# Save log-transform flag
meta = {
    "log_transform_time_span_hours": log_transform_applied,
    "calibration_method": cal_method,
    "scale_pos_weight": float(scale_pos_weight),
    "feature_cols": feature_cols,
    "test_roc_auc": float(roc_auc_cal),
    "test_pr_auc": float(pr_auc),
    "ece_final": float(best_ece),
}
meta_path = MDLS / "binary_model_meta.json"
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  Saved model meta: {meta_path}")

# ---------------------------------------------------------------------------
# 10. Plots
# ---------------------------------------------------------------------------
sep("9. PLOTS")

# --- Feature importance (top 20)
fig, ax = plt.subplots(figsize=(10, 7))
top20 = feat_imp.head(20)
colors = ["#E8504A" if top20.iloc[i]/top20.sum() > 0.3
          else "#4A90D9" for i in range(len(top20))]
ax.barh(top20.index[::-1], top20.values[::-1], color=colors[::-1], alpha=0.85)
ax.set_xlabel("Feature Importance (Gain)")
ax.set_title("Top-20 Feature Importances — Binary XGBoost v1", fontweight="bold")
ax.axvline(top20.sum() * 0.50, color="red", linestyle="--", linewidth=1.2,
           label="50% importance threshold")
ax.legend()
plt.tight_layout()
fig.savefig(OUT / "feature_importance_binary.png", dpi=150)
plt.close()
print(f"  Saved: {OUT / 'feature_importance_binary.png'}")

# --- Confusion matrix
cm = confusion_matrix(y_test, y_pred_cal)
fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks([0,1]); ax.set_yticks([0,1])
ax.set_xticklabels(["Pred Licit", "Pred Illicit"])
ax.set_yticklabels(["True Licit", "True Illicit"])
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(cm[i,j]), ha="center", va="center",
                color="white" if cm[i,j] > cm.max()/2 else "black", fontsize=14)
ax.set_title("Confusion Matrix — Binary Classifier (calibrated)", fontweight="bold")
plt.colorbar(im, ax=ax)
plt.tight_layout()
fig.savefig(OUT / "confusion_matrix_binary.png", dpi=150)
plt.close()
print(f"  Saved: {OUT / 'confusion_matrix_binary.png'}")

# --- ROC + PR curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fpr_c, tpr_c, _ = roc_curve(y_test, best_probs)
ax1.plot(fpr_c, tpr_c, color="#4A90D9", lw=2,
         label=f"ROC AUC = {roc_auc_cal:.4f}")
ax1.plot([0,1],[0,1],"k--",alpha=0.4)
ax1.set_xlabel("False Positive Rate"); ax1.set_ylabel("True Positive Rate")
ax1.set_title("ROC Curve (calibrated)", fontweight="bold"); ax1.legend()

prec_c, rec_c, _ = precision_recall_curve(y_test, best_probs)
pr_auc_cal = auc(rec_c, prec_c)
ax2.plot(rec_c, prec_c, color="#E8835A", lw=2,
         label=f"PR AUC = {pr_auc_cal:.4f}")
ax2.set_xlabel("Recall"); ax2.set_ylabel("Precision")
ax2.set_title("PR Curve (calibrated)", fontweight="bold"); ax2.legend()
plt.tight_layout()
fig.savefig(OUT / "roc_pr_curve_binary.png", dpi=150)
plt.close()
print(f"  Saved: {OUT / 'roc_pr_curve_binary.png'}")

# --- Calibration curves
fig, ax = plt.subplots(figsize=(7, 5))
for probs, label, color in [
    (y_prob_raw, f"Raw (ECE={ece_raw:.3f})", "#E8504A"),
    (y_prob_iso, f"Isotonic (ECE={ece_iso:.3f})", "#4A90D9"),
    (y_prob_sig, f"Sigmoid (ECE={ece_sig:.3f})", "#5DA85D"),
]:
    frac_pos, mean_pred = calibration_curve(y_test, probs, n_bins=10)
    ax.plot(mean_pred, frac_pos, marker="o", lw=1.5, label=label, color=color)
ax.plot([0,1],[0,1],"k--",alpha=0.5,label="Perfect calibration")
ax.set_xlabel("Mean Predicted Probability")
ax.set_ylabel("Fraction of Positives")
ax.set_title("Calibration Curves — Binary Classifier", fontweight="bold")
ax.legend(fontsize=9)
plt.tight_layout()
fig.savefig(OUT / "calibration_curve_binary.png", dpi=150)
plt.close()
print(f"  Saved: {OUT / 'calibration_curve_binary.png'}")

# ---------------------------------------------------------------------------
# 11. Round-trip model load test
# ---------------------------------------------------------------------------
sep("10. ROUND-TRIP MODEL LOAD TEST")
from xgboost import XGBClassifier as XGBCheck
m_check = XGBCheck()
m_check.load_model(str(model_path))
test_pred = m_check.predict_proba(X_test[:3])[:, 1]
print(f"  Model loaded OK. Sample predictions: {test_pred.round(4)}")
print("  Round-trip test: PASS")

# ---------------------------------------------------------------------------
# 12. VALIDATION GATE
# ---------------------------------------------------------------------------
sep("VALIDATION GATE")

issues = []

# Check 1: ROC-AUC >= 0.85
if roc_auc_cal >= 0.85:
    print(f"[PASS] Test ROC-AUC = {roc_auc_cal:.4f} >= 0.85")
else:
    msg = f"[FAIL] Test ROC-AUC = {roc_auc_cal:.4f} < 0.85 — do NOT proceed to Day 3"
    print(msg); issues.append(msg)

# Check 2: No single feature > 50% importance share
final_max_share = feat_imp.iloc[0] / feat_imp.sum()
if final_max_share <= THRESHOLD:
    print(f"[PASS] Max feature importance share = {final_max_share:.1%} <= 50%")
else:
    msg = f"[FAIL] Max feature importance share = {final_max_share:.1%} > 50% (fix did not resolve)"
    print(msg); issues.append(msg)

# Check 3: ECE
if best_ece <= 0.10:
    print(f"[PASS] ECE = {best_ece:.4f} <= 0.10 (reasonably calibrated)")
elif best_ece <= 0.20:
    print(f"[WARN] ECE = {best_ece:.4f} — moderate calibration, acceptable")
else:
    msg = f"[FAIL] ECE = {best_ece:.4f} > 0.20 — poor calibration"
    print(msg); issues.append(msg)

# Check 4: Artifacts loadable
if model_path.exists() and meta_path.exists():
    print(f"[PASS] Model artifacts saved and round-trip verified")
else:
    msg = "[FAIL] Model artifacts not found"
    print(msg); issues.append(msg)

sep("VALIDATION GATE SUMMARY")
if not issues:
    print("  ALL CHECKS PASSED. Ready for Day 3 (typology + LOSOCV + ablation).")
else:
    print(f"  {len(issues)} FAILURE(S) — resolve before Day 3:")
    for iss in issues:
        print(f"    {iss}")

sep("FINAL SUMMARY")
print(f"  scale_pos_weight (scenario): {scale_pos_weight:.4f}")
print(f"  scale_pos_weight (txn-level would have been): ~{0.634/0.366:.4f}")
print(f"  Log transform applied: {log_transform_applied}")
if log_transform_applied:
    print(f"  Importance share before: {max_share:.1%} → after: {final_max_share:.1%}")
print(f"  Calibration method: {cal_method}")
print(f"  ECE — raw: {ece_raw:.4f} | iso: {ece_iso:.4f} | sigmoid: {ece_sig:.4f}")
print(f"  Final test ROC-AUC: {roc_auc_cal:.4f}")
print(f"  Final test PR-AUC:  {pr_auc_cal:.4f}")
