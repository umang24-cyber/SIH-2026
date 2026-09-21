# V9 Calibration Gate Governance & Evaluation Architecture Report

**Document ID**: `docs/PHASE4_CALIBRATION_GATE_DECISION.md`  
**Repository**: SIH-2026 Bitcoin AML / Forensic ML Pipeline  
**Dataset Version**: V9.0 Corrected (`seed=20260921`, 5,440 scenarios, 167,749 transactions)  
**Evaluation Target**: Frozen Test Set (1,088 scenarios: 640 licit, 448 illicit)  
**Governance Date**: September 21, 2026  

---

## 1. Executive Decision

### Calibration Gate Governance Decision:
# CALIBRATION GATE: FORMALLY RESOLVED — TWO-TIER ARCHITECTURE APPROVED

### Phase 5 Retraining Status:
# PHASE 5: AUTHORIZED FOR DEVELOPMENT / RETRAINING

#### Executive Summary
Following a comprehensive feasibility review of binary probability calibration across seven candidate approaches on the corrected V9 benchmark, the following governance determinations are formally established **prior to Phase 5 retraining**:

1. **Original Gate Failure Confirmed**: The current scratch binary XGBoost model strictly fails the original locked calibration criteria (ECE <= 0.010, Brier <= 0.015), as do all tested post-hoc calibration methods (Platt, Platt on logit, Isotonic, Temperature, Beta).
2. **Methodological Conflation Identified**: Feasibility analysis demonstrates that Brier score combines classification accuracy / discrimination with probability reliability. At the 0.50 decision threshold, the 28 misclassified scenarios contribute 0.013358 to the observed Brier score, representing 73.76% of the total Brier score. This is a threshold-conditional diagnostic decomposition, not the standard Murphy Brier decomposition.
3. **No Calibration-Hunting**: Searching for more post-hoc calibration algorithms is mathematically unjustified and is officially terminated.
4. **Two-Tier Architecture Formally Approved**:
   - **Gate A (Discrimination)**: **APPROVED — FORMAL ACCEPTANCE GATE**. Primary model acceptance gate evaluating separation of licit vs. illicit scenarios using approved V9 blueprint thresholds.
   - **Gate B (Probability Quality)**: **APPROVED — REPORTING / DIAGNOSTIC TIER**. Mandatory reporting tier describing continuous risk score quality; does NOT independently determine model acceptance.
5. **Original Calibration Gate Historically Failed & Retired**: The original conjunctive requirement (ECE <= 0.010 AND Brier <= 0.015) historically **FAILED** and is formally retired as a standalone acceptance criterion.
6. **Proposed Numerical Gate B Thresholds Retired from Acceptance**: Candidate thresholds (ECE <= 0.015, Adaptive ECE <= 0.010, Brier <= 0.020, Cox slope [0.80, 1.25], Cox intercept [-0.50, +0.50]) are **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9**; they are retained solely as historical/reference candidates.
7. **Frozen Test Policy Locked**: The frozen test set remains strictly isolated and cannot be used for model selection, threshold tuning, or hyperparameter optimization. Phase 5 production development and retraining is **AUTHORIZED FOR DEVELOPMENT / RETRAINING** under this locked protocol.


---

## 2. Original Locked Gate

The original Phase 4 acceptance criteria for probability calibration were specified as a conjunctive gate:
- **Locked ECE Gate**: ECE <= 0.010 (10 equal-width uniform bins)
- **Locked Brier Gate**: Brier Score <= 0.015

### Status:
# FAIL

Neither raw XGBoost nor any post-hoc calibrated model met both thresholds simultaneously on the frozen test set.

---

## 3. Current Frozen-Test Results

The candidate binary model (trained on the proper training split `X_proper`, `y_proper` with early stopping on `X_eval`, `y_eval`) was evaluated on the 1,088 frozen test scenarios:

### Summary of Evaluated Methods (Test Descriptive Metrics)

| Calibration Method | 10-Bin Equal-Width ECE | Brier Score | ROC-AUC | PR-AUC | Balanced Accuracy | Original Gate Status |
|---|---|---|---|---|---|---|
| **Original Locked Gate** | **<= 0.010000** | **<= 0.015000** | **>= 0.9850** | **>= 0.9800** | **>= 0.9400** | — |
| **RAW XGBoost** | 0.012526 | 0.018111 | 0.997489 | 0.996720 | 0.971763 | **FAIL** |
| **Platt Scaling (Prob)** | 0.014391 | 0.019766 | 0.997489 | 0.996720 | 0.971763 | **FAIL** |
| **Platt Scaling (Logit)** | 0.011319 | 0.019088 | 0.997489 | 0.996720 | 0.971763 | **FAIL** |
| **Isotonic Regression** | 0.011025 | 0.020104 | 0.996395 | 0.994468 | 0.971763 | **FAIL** |
| **Temperature Scaling (T=0.9306)** | 0.012361 | 0.018024 | 0.997489 | 0.996720 | 0.971763 | **FAIL** |
| **Beta Calibration (C=1.0)** | 0.013267 | 0.018921 | 0.997489 | 0.996720 | 0.971763 | **FAIL** |
| **Oracle Test-Fitted Isotonic** *(Diagnostic Only)* | 1.66e-9 | 0.015488 | 0.996395 | 0.994468 | 0.971763 | **FAIL** |

*Note*: The values in this table describe the performance of the candidate models on the frozen test set; they are diagnostic observations and do not establish acceptance thresholds.

---

## 4. Calibration Feasibility Findings

The feasibility review established three concrete empirical findings:

1. **Post-Hoc Calibration Does Not Solve the Failure**:
   - Platt scaling on probabilities increases Brier from 0.018111 to 0.019766.
   - Platt scaling on logits slightly reduces ECE (0.011319) but worsens Brier (0.019088).
   - Isotonic regression achieves the lowest equal-width ECE (0.011025) but worsens Brier (0.020104).
   - Temperature scaling slightly reduces Brier (0.018024) but leaves ECE above threshold (0.012361).
   - Beta calibration yields ECE = 0.013267 and Brier = 0.018921.
2. **Post-Hoc Methods Preserve Ranking Inversions**:
   - Monotonic calibration preserves the relative ordering of scores.
   - When licit scenarios have higher model scores than illicit scenarios (ranking inversions / classification errors), no monotonic transformation can eliminate the squared error penalty associated with those inversions.
3. **Algorithm Searching is Counter-Productive**:
   - Searching for increasingly exotic calibration algorithms risks p-hacking against the test set and cannot address the underlying error structure.

---

## 5. Brier Interpretation

The Brier score is defined as:

$$\text{Brier} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

### Methodological Classification: Overall Probabilistic Scoring Metric
- **Brier is an overall probabilistic scoring metric, NOT a pure calibration metric**. It combines probability forecast quality with the model's ability to resolve/separate outcomes.
- **Error Dominance**:
  - In the frozen test set, there are 28 classification errors (at the 0.50 decision threshold): 9 false positives and 19 false negatives.
  - At the 0.50 decision threshold, the 28 misclassified scenarios contribute **0.013358** to the observed Brier score, representing **73.76%** of the total Brier score.
  - This is a threshold-conditional diagnostic decomposition, not the standard Murphy Brier decomposition.
  - The 1,060 correctly classified scenarios contribute only **0.004754** (26.24%).
- **Governance Finding**:
  - Failing a Brier threshold does not by itself prove that probability calibration is poor.
  - Therefore, the original Brier <= 0.015 criterion is not suitable to interpret as a standalone calibration criterion without additional justification.
  - Any future Brier threshold requires an explicit governance decision and must be evaluated as an overall probabilistic score, not as a proxy for calibration.

---

## 6. ECE Interpretation

Expected Calibration Error with M equal-width bins partitions [0, 1] into uniform intervals:

$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

### Evaluation Across Equal-Width Binnings:

| Number of Bins | RAW ECE | Isotonic ECE | Extreme Bin Share ([0, 0.1) U [0.9, 1.0]) |
|---|---|---|---|
| **5 Bins** | 0.011857 | 0.010140 | 95.1% (1,035 / 1,088) |
| **10 Bins** | 0.012526 | 0.011025 | 91.8% (999 / 1,088) |
| **15 Bins** | 0.017301 | 0.011003 | 88.7% (965 / 1,088) |
| **20 Bins** | 0.019203 | 0.014027 | 87.0% (946 / 1,088) |

### Key Methodological Findings:
1. **ECE Remains Above 0.010 Across Tested Equal-Width Binnings**: In none of the tested 5, 10, 15, or 20 equal-width bin configurations does RAW or Isotonic reach <= 0.010.
2. **Prediction Polarization**: Over 91.8% of test scenarios have predicted probabilities < 0.10 or >= 0.90.
3. **Bin Sparsity Artifact**: The intermediate 8 bins (0.10 <= p < 0.90) share fewer than 90 samples total (e.g., bin [0.4, 0.5) has only 7 samples). A small number of discrete errors in sparse bins creates large empirical frequency gaps (|acc - conf| = 0.25 to 0.40).
4. **Governance Finding**:
   - Equal-width ECE should not be treated as a completely binning-independent ground truth.
   - Adaptive ECE is included as a complementary calibration diagnostic because equal-frequency bins reduce sparse intermediate-bin instability. Its use as a formal acceptance criterion requires governance approval.

---

## 7. Murphy Decomposition

Under the Murphy (1973) three-component decomposition on 10 uniform bins:

$$\text{Brier} \approx \text{Reliability} - \text{Resolution} + \text{Uncertainty}$$

Evaluated on the frozen test set:

| Decomposition Component | RAW XGBoost | Isotonic Regression | Methodological Interpretation |
|---|---|---|---|
| **Uncertainty** (y_bar * (1 - y_bar)) | 0.242215 | 0.242215 | Variance of test set illicit rate (41.18%). |
| **Resolution** (sum n_k (y_k - y_bar)^2 / N) | 0.225449 | 0.223269 | Discrimination power: sorting of samples into pure bins. |
| **Uncertainty - Resolution** | **0.016765** | **0.018946** | **Residual discrimination/resolution component**. |
| **Reliability** (sum n_k (p_k - y_k)^2 / N) | **0.001565** | **0.001268** | **Binned calibration discrepancy**. |
| **Sum (Decomposed Brier)** | 0.018330 | 0.020214 | Reliability + (Uncertainty - Resolution). |
| **Actual Brier Score** | **0.018111** | **0.020104** | Within discretization residual (< 0.00022). |

### Diagnostic Language and Interpretation:
- Under the stated 10-bin Murphy decomposition, the residual Uncertainty - Resolution component is approximately **0.016765**, indicating that the observed Brier score contains a substantial discrimination/resolution component in addition to the binned reliability component.
- The binned reliability term is **0.001565** (RAW) and **0.001268** (Isotonic).
- *Important Qualification*: This decomposition is a useful diagnostic to separate sorting from probability assignment, but it is bin-dependent. It must not be cited as a universal lower bound on Brier for arbitrary future probability predictions, nor as a proof that calibration is "exceptional."

---

## 8. Oracle Isotonic Diagnostic

To explore the theoretical properties of the frozen test ranking, an unconstrained isotonic regression was fitted directly on the test labels:

$$\text{Brier}_{\text{test\_iso}} = 0.015488$$

### Strict Scope and Interpretation:
- **Diagnostic Only — Not a Valid Deployment Calibrator**:
  - For the frozen test prediction vector, test-label-fitted isotonic regression gives the minimum squared-error score among non-decreasing mappings of those prediction values. This is a diagnostic oracle and is not a deployable calibrator.
- **Explicit Limitations**:
  - It must **NEVER** be used as a deployable calibrator or as training data.
  - It is **NOT** a universal lower bound for all calibration procedures or future models.
  - It must **NOT** be used for model selection.
  - It must **NOT** be used to justify a new numerical gate.

---

## 9. Leakage Audit

A comprehensive audit was performed across all datasets, splits, and training scripts:

| Verification Item | Result | Evidence |
|---|---|---|
| **1. Test labels in production model** | **PASS** | `train_v9.py` fits strictly on `X_proper, y_proper`. Frozen test is strictly read-only for final evaluation. |
| **2. Test labels in deployable calibrators** | **PASS** | All calibrator variants fit strictly on `cal_raw, y_cal` (653 calibration holdout scenarios). |
| **3. Calibration & Proper Train overlap** | **PASS** | `len(set(idx_proper) & set(idx_cal)) = 0`. Disjoint splits. |
| **4. Calibration & Frozen Test overlap** | **PASS** | `len(set(df_cal.scenario_id) & set(df_test.scenario_id)) = 0`. Disjoint splits. |
| **5. Scenario ID overlap across all splits** | **PASS** | Proper train (3,046), Eval (653), Cal (653), Test (1,088) are pairwise disjoint. |
| **6. Transaction ID (TXID) overlap** | **PASS** | Train TXIDs (132,997) & Test TXIDs (34,752) = empty set (0 overlap). |
| **7. Target / proxy feature exclusion** | **PASS** | `FORBIDDEN_FEATURES = {'is_illicit', 'pattern_type', 'scenario_id', 'split', 'is_licit_exchange'}` strictly excluded. |
| **8. Feature count and schema order** | **PASS** | Exactly 46 feature columns in identical order across train and test matrices. |
| **9. V8 codebase integrity** | **PASS** | Zero modifications to any V8 scripts or datasets. |
| **10. Model artifact status check** | **PASS** | Production artifacts in `ml/models/` (dated 2026-09-20T17:19:28) correctly identified as stale pre-remediation artifacts. |

**Audit Conclusion**: Leakage audit **PASSES** completely.

---

## 10. Layering Error Analysis

Investigation of the 28 classification errors on the frozen test set revealed a concentrated error structure:

### Error Breakdown by Typology

| Typology | Total Test Scenarios | Classification Errors | Error Type | Typology Error Rate |
|---|---|---|---|---|
| **Licit (Normal)** | 640 | 9 | False Positive (y=0, y_hat=1) | 1.41% |
| **Ransomware** | 112 | **0** | False Negative (y=1, y_hat=0) | **0.00%** |
| **Peeling Chain** | 112 | **0** | False Negative (y=1, y_hat=0) | **0.00%** |
| **Mixing** | 112 | **0** | False Negative (y=1, y_hat=0) | **0.00%** |
| **Layering** | 112 | **19** | False Negative (y=1, y_hat=0) | **16.96%** |

### Characteristics:
- **100% of False Negatives (19/19) are layering scenarios**.
- Ransomware, peeling chains, and mixing have zero false negatives (100% detection rate).
- Most layering false negatives have borderline probabilities (p between 0.11 and 0.49) rather than extreme licit confidence.
- On the internal training-split validation set (N=653), the model similarly produced 17 false negatives, all 17 of which were layering.

### Strict Governance Rule on Layering Errors:
- The frozen test errors are diagnostic observations.
- **DO NOT** modify the V9 generator specifically to eliminate these 19 known frozen-test cases.
- **DO NOT** add features because they improve those specific test cases.
- **DO NOT** tune hyperparameters using them.
- All development decisions must use train/validation data only. The frozen test set remains untouched.
- The development objective is: *"Improve generalization of layering-vs-licit discrimination using development data."*

---

## 11. Formally Approved Two-Tier Evaluation Architecture

The two-tier evaluation architecture is **FORMALLY APPROVED BY GOVERNANCE**:

```text
+------------------------------------------------------------------------+
|                GOVERNANCE-APPROVED TWO-TIER ARCHITECTURE               |
+------------------------------------+-----------------------------------+
| GATE A: FORMAL ACCEPTANCE GATE     | GATE B: REPORTING/DIAGNOSTIC TIER |
| (Separation of Licit vs Illicit)   | (Reliability of Risk Scores)      |
+------------------------------------+-----------------------------------+
| • ROC-AUC                          | • Reliability Diagram             |
| • PR-AUC                           | • Cox Calibration Slope           |
| • Balanced Accuracy                | • Cox Calibration Intercept       |
| • F1 / Macro-F1                    | • Equal-Width 10-Bin ECE          |
| • Size-Controlled Evaluation (OVL) | • Adaptive Equal-Frequency 10-Bin |
| • Generator-Shift Evaluation       | • Brier Score                     |
| • Typology Miss Rates / Matrix     | • Bootstrap Uncertainty (95% CI)  |
+------------------------------------+-----------------------------------+
```

### Conceptual Distinction & Governance Tiering:
- **Gate A (Formal Acceptance Gate)**: Evaluates whether the model separates licit and illicit scenarios. This is the **primary formal acceptance gate** for model deployment. It utilizes the existing project-approved V9 blueprint thresholds (ROC-AUC >= 0.985, PR-AUC >= 0.980, Balanced Accuracy >= 0.940).
- **Gate B (Reporting / Diagnostic Tier)**: Evaluates the quality and reliability of the continuous probability risk scores. For this V9 iteration, Gate B is **NOT a hard blocking acceptance gate**. Gate B metrics must be reported descriptively to document risk-score reliability, but they do not independently block model acceptance.
- **Independence of Concerns**:
  - A model may demonstrate strong discrimination while requiring probability-quality improvements.
  - Do not use one Brier threshold as a proxy for the entire ML model's quality.
  - Do not use calibration quality to erase discrimination errors.
  - Do not use high anomaly scores to compensate for poor binary risk.


---

## 12. Formal Retirement of the Original Calibration Interpretation

### Formal Governance Action:
The original conjunctive requirement:

$$\text{ECE} \le 0.010 \quad \text{AND} \quad \text{Brier} \le 0.015$$

**IS RETIRED AS A STANDALONE CALIBRATION GATE.**

### Rationale:
1. **Brier incorporates overall probabilistic scoring behavior**, including discrimination/resolution, and therefore cannot be interpreted as a pure calibration measure.
2. **Equal-width ECE is binning-dependent** and sensitive to intermediate-bin sample sparsity under extreme polarization; it should not be treated as a unique ground-truth calibration quantity.

### Historical Record:
- This action does **NOT** mean the candidate model passed the original gate.
- The historical fact remains: **ORIGINAL CALIBRATION GATE = FAILED**.
- The governance decision is that the original gate is not retained as the sole interpretation of probability calibration.

---

## 13. Metric Definitions & Rules Locked Now

The following definitions and rules are **LOCKED IMMEDIATELY**:

### Metric Definitions (Locked):
- **ROC-AUC**: Standard trapezoidal / Wilcoxon rank-sum area under ROC curve.
- **PR-AUC**: Average precision score computed over precision-recall curve.
- **Balanced Accuracy**: Macro-average of recall across licit and illicit classes.
- **F1 / Macro-F1**: Harmonic mean of precision and recall.
- **Size-Controlled Evaluation**: 1D decision tree AUC, mutual information, and OVL histogram overlap across scenario size distributions.
- **Generator-Shift Evaluation**: Evaluation on Gate B moderate size shift distribution.
- **Reliability Diagram**: 10 equal-width bins, plotting mean predicted probability vs empirical class frequency, with sample counts annotated.
- **Cox Logistic Calibration Parameters**: Univariate logistic regression on log-odds: $\text{logit}(P(Y=1)) = \alpha + \beta \cdot \text{logit}(\hat{p})$.
- **Equal-Width 10-Bin ECE**: Standard weighted gap across 10 uniform intervals.
- **Adaptive 10-Bin ECE**: Quantile-based 10-bin ECE with equal sample counts per bin.
- **Brier Score**: Mean squared probabilistic error: $\frac{1}{N}\sum (p_i - y_i)^2$.
- **Bootstrap Procedure**: 2,000 resamples with fixed seed (42) for diagnostic 95% confidence intervals.

### Dataset & Evaluation Rules (Locked):
- V9 corrected dataset (`seed=20260921`) remains frozen.
- Frozen test set remains untouched.
- Test labels cannot influence development.
- Scenario-level split remains mandatory.
- TXID overlap remains zero.
- Ground-truth fields remain excluded from features.
- Feature schema remains strictly 46 features.
- V8 codebase remains frozen.

### Governance Rules (Locked):
- No test-set threshold selection.
- No test-set feature selection.
- No test-set hyperparameter tuning.
- No test-set generator tuning.
- No test-set calibration-method selection.
- No test-set operating-point selection.

---

## 14. Gate B Numerical Thresholds Retired from Formal Acceptance

Governance has formally determined that numerical candidate thresholds for Gate B are **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9**.

### Gate B Numerical Status

| Metric | Proposed Candidate Threshold | Formal Governance Status |
|---|---|---|
| **Equal-Width ECE (10-bin)** | <= 0.015 | **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9. RETAINED ONLY AS HISTORICAL/REFERENCE CANDIDATES.** |
| **Adaptive ECE (10-bin)** | <= 0.010 | **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9. RETAINED ONLY AS HISTORICAL/REFERENCE CANDIDATES.** |
| **Brier Score** | <= 0.020 | **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9. RETAINED ONLY AS HISTORICAL/REFERENCE CANDIDATES.** |
| **Cox Calibration Slope (beta)** | [0.80, 1.25] | **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9. RETAINED ONLY AS HISTORICAL/REFERENCE CANDIDATES.** |
| **Cox Calibration Intercept (alpha)** | [-0.50, +0.50] | **NOT USED AS HARD ACCEPTANCE THRESHOLDS FOR V9. RETAINED ONLY AS HISTORICAL/REFERENCE CANDIDATES.** |

### Governance Policy on Gate B Thresholds:
- These numerical candidate values are **NOT formal acceptance gates** for V9.
- Gate B is designated as a mandatory **REPORTING / DIAGNOSTIC TIER**.
- Do **NOT** claim the model passes or fails these as a formal Gate B acceptance test.
- The metrics will be computed and reported descriptively to monitor continuous risk-score reliability and maintain complete methodological transparency.

---

## 15. Decision Threshold Governance

- The binary decision threshold does **NOT** need to remain 0.50 if the approved operating objective eventually calls for another operating point.
- However, **do NOT choose an arbitrary threshold (e.g. 0.42) now**.
- **Rule**: The decision threshold may be selected on the designated validation/development split using a predeclared operating objective (e.g., balanced accuracy, constrained false-positive rate, constrained false-negative rate, or predefined investigation cost) and then frozen before final test evaluation.
- For now, the existing **0.50 threshold is retained** unless the approved Phase 5 development plan explicitly specifies another operating point.

---

## 16. Architecture C Preservation

The approved V9 Architecture C remains strictly preserved:

```text
                  Scenario Transaction & Network Records
                                     │
                                     ▼
                      46 Scenario-Level Features
                                     │
                                     ▼
                            Binary XGBoost
                                     │
                         P(illicit) / Risk Score
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
         Risk Score < 0.5                        Risk Score >= 0.5
            [Licit]                                  [Illicit]
                                                         │
                                                         ▼
                                              Multi-Class Typology XGBoost
                                              (Ransomware / Peeling /
                                               Layering / Mixing)
                                                         │
                                                         ▼
                                               Forensic Evidence Dossier
                                               (SHAP + Graph Evidence)
```

### Architectural Constraints Upheld:
1. **Binary Risk is the Primary Gate**: No scenario bypasses binary risk to enter typology classification.
2. **Contextual Isolation Forest**: Isolation Forest is used solely as an auxiliary contextual measure of transactional unusualness; it does not override binary classification.
3. **Prohibition of Composite Logic**: Do NOT implement `anomaly OR risk → illicit`. Anomaly scores cannot compensate for low binary risk.
4. **No Typology-Based Ranking**: Do NOT rank Top-N alerts by typology confidence; alerts must be prioritized by binary risk.
5. **No Shortcut Ingestion**: No candidate transaction fragments (1–3 txns) are scored with the scenario model.
6. **Investigation Semantics**: `risk_score` is strictly defined as *"model-estimated likelihood/confidence that the scenario is illicit, used for investigative prioritization."* It is never presented as legal proof or ownership attribution.

---

## 17. Governance Decision Record

The formal governance determinations prior to Phase 5 retraining are recorded as follows:

1. **Gate A (Discrimination Gate)**:  
   **APPROVED — FORMAL ACCEPTANCE GATE** according to existing project blueprint specification.
2. **Gate B (Probability Quality Tier)**:  
   **APPROVED — REPORTING / DIAGNOSTIC TIER** (Mandatory descriptive reporting; not a hard blocking acceptance gate for V9).
3. **Gate B Numerical Thresholds**:  
   **NOT USED AS HARD V9 ACCEPTANCE THRESHOLDS** (Retained only as historical/reference candidates).
4. **Original Calibration Gate**:  
   **HISTORICALLY FAILED / RETIRED** as a standalone acceptance criterion.
5. **Frozen Test Policy**:  
   **LOCKED** (Strictly isolated; used solely for final descriptive evaluation and CI reporting).
6. **Architecture C**:  
   **LOCKED** (Strict scenario-level inference; contextual Isolation Forest; no shortcut ingestion; alerts ranked by binary risk).
7. **Phase 5 Production Retraining**:  
   **AUTHORIZED FOR DEVELOPMENT / RETRAINING** under the frozen evaluation protocol.

---

## 18. Phase 5 Development Protocol & Implementation Order

### Development Protocol:
1. **Data Split Progression**:
   ```text
   PROPER TRAIN (3,046 scenarios)
          ↓
   VALIDATION / EARLY STOPPING (653 scenarios)
          ↓
   CALIBRATION HOLDOUT (653 scenarios)
          ↓
   FROZEN TEST (1,088 scenarios) — FINAL EVALUATION ONLY
   ```
2. **Frozen Test Isolation**:
   - The frozen test set remains strictly untouched until the development protocol is fully executed.
3. **Binary Model Objective**:
   - Primary objective: Improve generalization of licit-vs-illicit scenario discrimination.
   - Known development finding: Layering scenarios historically produced concentrated false negatives.
   - Strict constraint: **DO NOT optimize specifically against the known 19 frozen-test layering cases**.
   - Investigation must use **TRAIN / VALIDATION DATA ONLY** to improve layering-vs-licit separation.
4. **Typology Model Objective**:
   - Train multi-class model on illicit scenarios only (`ransomware`, `peeling_chain`, `layering`, `mixing`).
   - Strictly prohibit ground-truth labels or generator metadata from features.
5. **Calibration Protocol**:
   - Do not perform test-set calibration.
   - If post-hoc calibration is retained, fit it only on the designated calibration holdout (`X_cal`, `y_cal`).
   - Report Gate B metrics descriptively; do not select a calibration method because it performs best on the frozen test.
6. **Model Selection Rule**:
   - The development model must be selected using **TRAIN + VALIDATION / DEVELOPMENT DATA ONLY**.
   - Do NOT compare candidate models using frozen-test performance to choose the final model.
   - The frozen test is evaluated **ONCE** after architecture, features, hyperparameters, calibration, and decision threshold are frozen.
7. **Decision Threshold**:
   - Retain default decision threshold: $P(\text{illicit}) \ge 0.50$ unless a different operating point is explicitly selected on validation data under a predeclared objective.

### Pre-Training Safety Verification:

Prior to launching Phase 5 training, all safety and integrity constraints were audited and verified:

| Check Item | Target Specification | Actual Status | Result |
|---|---|---|---|
| **V9 Dataset Seed** | `20260921` | Seed 20260921 confirmed in generator and data | **PASS** |
| **Total Scenario Count** | 5,440 scenarios | 4,352 train + 1,088 test = 5,440 | **PASS** |
| **Total Transaction Count**| 167,749 transactions | 132,997 train + 34,752 test = 167,749 | **PASS** |
| **Scenario Overlap** | Exactly 0 | 0 overlapping scenario IDs between train/test | **PASS** |
| **TXID Overlap** | Exactly 0 | 0 overlapping TXIDs between train/test | **PASS** |
| **Feature Schema** | Strictly 46 features | Exactly 46 numerical scenario features | **PASS** |
| **Ground-Truth Leakage** | 0 forbidden columns | Excluded: label, scenario_id, typology, etc. | **PASS** |
| **Frozen Test Integrity** | Bit-for-bit unchanged | Sizes (692,043 / 30,064 bytes) and hashes verified | **PASS** |
| **Test Label Isolation** | No test labels in train | Enforced by proper training split | **PASS** |
| **Calibration Isolation** | No test labels in cal | Calibrator fit on X_cal holdout only | **PASS** |
| **Threshold Independence** | No test-set tuning | Default 0.50 threshold retained | **PASS** |

### Phase 5 Implementation Sequence:
1. **Freeze V9 evaluation protocol** *(Complete)*.
2. **Train corrected V9 binary model** on `X_proper` with early stopping on `X_eval`.
3. **Train corrected V9 typology model** on illicit subset of `X_proper`.
4. **Evaluate on development/validation data** (`X_eval`, `y_eval`).
5. **Perform development-only error analysis** (focusing on layering discrimination).
6. **Perform development-only calibration fitting** (if retained, on `X_cal`).
7. **Freeze final model + threshold + calibration procedure**.
8. **Verify frozen-test isolation** prior to test execution.
9. **Evaluate frozen test ONCE**.
10. **Produce final Gate A + Gate B report**.
11. **Integrate final artifacts into backend inference** (`ml/models/`).

---

## 19. Repository Provenance Audit & Reconciliation

To ensure strict provenance auditability, this section classifies every modified or untracked file currently present in the working tree.

### Provenance Classification Table

| Path | Git Status | Provenance Category | Evidence / Details |
|---|---|---|---|
| `docs/PHASE4_CALIBRATION_GATE_DECISION.md` | Untracked File | **Created/Modified by THIS task** | Governance decision record and evaluation protocol freeze document (Created 2026-09-21 15:05 UTC). |
| `cli/bitkaun.egg-info/SOURCES.txt` | Modified (Tracked) | **Pre-existing / Unrelated working-tree modification** | Modified on 2026-09-10 08:39:47 UTC during earlier CLI setup/packaging work; pre-dates Phase 4 by 10+ days. Unrelated to governance task. Untouched by this task. |
| `run_ubuntu.sh` | Modified (Tracked) | **Pre-existing / Unrelated working-tree modification** | Modified on 2026-09-10 08:40:06 UTC to support conda environment activation; pre-dates Phase 4 by 10+ days. Unrelated to governance task. Untouched by this task. |
| `data/processed_v9/` | Untracked Directory | **Pre-existing Phase-4 Artifact** | Corrected V9 dataset (`seed=20260921`, 5,440 scenarios, 167,749 txns) generated 2026-09-20 18:15–18:17 UTC during Phase 4 generator remediation. Untouched by this task. |
| `data/processed_v9_gate_b_moderate/` | Untracked Directory | **Pre-existing Phase-4 Artifact** | Moderate size-shift benchmark dataset generated 2026-09-20 17:50:58 UTC during Phase 4 audit. Untouched by this task. |
| `data/processed_v9_gate_b_adv/` | Untracked Directory | **Pre-existing Phase-4 Artifact** | Adversarial size-shift benchmark dataset generated 2026-09-20 17:53:40 UTC during Phase 4 audit. Untouched by this task. |
| `data_pipeline/generate_v9.py` | Untracked File | **Pre-existing Phase-4 Artifact** | Remediation generator script modified 2026-09-20 18:08:27 UTC during Phase 4 remediation implementation. Untouched by this task. |
| `ml/train_v9.py` | Untracked File | **Pre-existing Phase-4 Artifact** | Training script created 2026-09-20 17:19:14 UTC during initial Phase 4 setup. Untouched by this task. |
| `ml/manifests/MANIFEST_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Pipeline manifest generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |
| `ml/models/binary_model_v9.ubj` | Untracked File | **Pre-existing Phase-4 Artifact** | Binary model artifact generated 2026-09-20 17:19:28 UTC. Stale pre-remediation artifact preserved; NO retraining performed. Untouched by this task. |
| `ml/models/binary_model_v9.xgb` | Untracked File | **Pre-existing Phase-4 Artifact** | Binary model artifact generated 2026-09-20 17:19:28 UTC. Stale pre-remediation artifact preserved; NO retraining performed. Untouched by this task. |
| `ml/models/typology_model_v9.ubj` | Untracked File | **Pre-existing Phase-4 Artifact** | Typology model artifact generated 2026-09-20 17:19:33 UTC. Stale pre-remediation artifact preserved; NO retraining performed. Untouched by this task. |
| `ml/models/typology_model_v9.xgb` | Untracked File | **Pre-existing Phase-4 Artifact** | Typology model artifact generated 2026-09-20 17:19:33 UTC. Stale pre-remediation artifact preserved; NO retraining performed. Untouched by this task. |
| `ml/reports/ablation_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Metric report generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |
| `ml/reports/binary_metrics_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Metric report generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |
| `ml/reports/error_analysis_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Metric report generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |
| `ml/reports/feature_importance_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Metric report generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |
| `ml/reports/typology_metrics_v9.json` | Untracked File | **Pre-existing Phase-4 Artifact** | Metric report generated 2026-09-20 17:19:42 UTC during initial Phase 4 run. Untouched by this task. |

### Separation of Concepts:
1. **Files Modified/Created by THIS Governance Task**:
   - `docs/PHASE4_CALIBRATION_GATE_DECISION.md` is the only file created and modified during this governance task.
2. **Pre-Existing Working-Tree Modifications**:
   - `cli/bitkaun.egg-info/SOURCES.txt` and `run_ubuntu.sh` are pre-existing working-tree modifications from September 10, 2026. They are completely unrelated to ML pipeline development and were not touched by this task.
   - The untracked `data/processed_v9*`, `data_pipeline/generate_v9.py`, and `ml/*` artifacts were created during earlier Phase 4 phases (September 20, 2026). They are not newly created files of this governance task.
3. **Files Confirmed Untouched by THIS Task**:
   - V8 codebase (`data/processed/`, `ml/train_v8*.py`): Untouched.
   - V9 generator (`data_pipeline/generate_v9.py`): Untouched.
   - V9 corrected dataset (`data/processed_v9/`): Untouched.
   - Frozen test set labels and features (`scenario_features_full_test.csv`, `scenario_labels_test.csv`): Untouched.
   - Production model artifacts (`ml/models/binary_model_v9.*`, `ml/models/typology_model_v9.*`): Untouched. Stale pre-remediation models preserved without retraining.
   - V9 training code (`ml/train_v9.py`): Untouched.

---

## 20. Git Verification

```bash
$ git status --short
 M cli/bitkaun.egg-info/SOURCES.txt
 M run_ubuntu.sh
?? data/processed_v9/
?? data/processed_v9_gate_b_adv/
?? data/processed_v9_gate_b_moderate/
?? data_pipeline/generate_v9.py
?? docs/PHASE4_CALIBRATION_GATE_DECISION.md
?? ml/manifests/MANIFEST_v9.json
?? ml/models/binary_model_v9.ubj
?? ml/models/binary_model_v9.xgb
?? ml/models/typology_model_v9.ubj
?? ml/models/typology_model_v9.xgb
?? ml/reports/ablation_v9.json
?? ml/reports/binary_metrics_v9.json
?? ml/reports/error_analysis_v9.json
?? ml/reports/feature_importance_v9.json
?? ml/reports/typology_metrics_v9.json
?? ml/train_v9.py

$ git diff --stat
 cli/bitkaun.egg-info/SOURCES.txt | 17 +++++++++++++++++
 run_ubuntu.sh                    |  9 ++++++++-
 2 files changed, 24 insertions(+), 2 deletions(-)

$ git diff --check
[Clean — 0 whitespace or syntax errors]
```

### Working Tree Provenance Statement:
Repository provenance audit: the governance documentation file (`docs/PHASE4_CALIBRATION_GATE_DECISION.md`) was created and modified by this task. The working tree also contains pre-existing/unrelated tracked modifications (`cli/bitkaun.egg-info/SOURCES.txt`, `run_ubuntu.sh`) and pre-existing untracked V9 Phase-4 artifacts (`data/processed_v9*`, `data_pipeline/generate_v9.py`, `ml/*`). These were not modified by this governance task, subject to the provenance verification above. No production code or model artifacts were modified or retrained.
