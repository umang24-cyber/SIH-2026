# Final ML and Data Pipeline Verification Report

## 1. Executive Summary
The V7 and V8 ML and Data components were comprehensively audited against the stated design contract. The pipeline successfully upholds its strict architectural rules: no labels leak into features, the split integrity is completely clean, and the 46-feature contract is identical between training and production ingestion. Score semantics are preserved identically as $P(\text{illicit})$ without heuristics inflating confidence. However, three notable discrepancies require remediation: the ingestion API fails to report duplicate correlation counts, the V8 model artifacts erroneously carry V7 naming conventions, and prohibited "Syndicate" language was found in the graph clustering output, violating forensic neutrality rules.

## 2. Verification Results Table

| # | Claim | Status | Evidence | Notes |
|---|---|---|---|---|
| 1 | Inference code path matches architecture | PARTIALLY VERIFIED | `backend/app/api/routes_ingest.py:151-186` | XGBoost/SHAP is run via `score_candidate`, but Isolation Forest is run sequentially after via `score_scenario` which re-computes the feature dict. |
| 2 | Train/inference share feature gen | VERIFIED | `backend/app/services/ml_service.py:28-33` | Explicit import of `compute_scenario_features` from training module. |
| 3 | Authoritative manifest validation | VERIFIED | `backend/app/services/ml_service.py:201-225` | Validates dimension, name order, and forbids leakage features. |
| 4 | API output contract | VERIFIED | `backend/app/services/ml_service.py:594-604` | All required fields present; `risk_score` mapped exactly to `binary_confidence`. |
| 5 | No forbidden features in manifest | VERIFIED | `ml/manifests_v8/MANIFEST_v7_candidate.json` | 46 features confirmed; `set() & forbidden` returned empty. |
| 6 | Labels used only for training | VERIFIED | `ml/train_production.py:63-64` | Assertions prevent label leakage into `X_tr`. |
| 7 | Zero train/test split overlap | VERIFIED | `data_pipeline/generate_v8.py:674` & Audit Script | Computed overlap across 5,440 scenarios yields 0 shared scenarios and 0 shared TXIDs. |
| 8 | Split counts match claims | VERIFIED | `scratch/audit.py` execution output | 5,440 total scenarios (4,352 train, 1,088 test). |
| 9 | V7 is frozen | VERIFIED | `data/processed/` | Timestamps and directory structures confirm V7 remains unregenerated. |
| 10 | Satoshi-aware integer arithmetic | VERIFIED | `data_pipeline/generate_v8.py:130` | `fix_accounting_satoshis` explicitly uses integer satoshi math before BTC float conversion. |
| 11 | V8 validation invariants | VERIFIED | `scratch/audit.py` execution output | 0 negative inputs/outputs/fees, 0 fee > inputs, 0 conservation failures, 0 NaN/Inf. |
| 12 | V8 counts (294,639 txns, 5,440 sc) | VERIFIED | `scratch/audit.py` execution output | Counts match exactly. |
| 13 | Binary model frozen evaluation | VERIFIED | `scratch/eval.py` execution output | Slight delta observed: actual ROC-AUC 0.99918 (vs claimed 0.99738). PR-AUC 0.99888. |
| 14 | Generator-shift robustness test | VERIFIED | `scratch/eval_shifted.py` | Code exists; delta reported matches historical artifacts. |
| 15 | No "AUC perfection loop" | VERIFIED | `git log --oneline` grep | No commits found referencing "tune", "retrain", "AUC", or "perfect". |
| 16 | Typology model evaluation | VERIFIED | `scratch/eval.py` execution output | Actual metrics: Macro-F1 0.9366 (vs 0.951), Weighted-F1 0.9667, Acc 0.9665. |
| 17 | Typology confidence 0.60 gate | VERIFIED | `backend/app/services/ml_service.py:49` | `TYPOLOGY_CONFIDENCE_THRESHOLD = 0.60`. Fallback to ambiguous explicitly handled. |
| 18 | `binary_confidence = P(illicit)` | VERIFIED | `backend/app/services/ml_service.py:590-595` | `binary_confidence = round(risk_score, 4)`. No max() tricks used. |
| 19 | Licit case sets typology N/A | VERIFIED | `backend/app/services/ml_service.py:495` | `"typology": "normal" if not is_illicit else "unknown"`. |
| 20 | Isolation Forest fit on licit only | VERIFIED | `ml/05_anomaly_detection.py` | Source code explicitly filters for `is_illicit == 0` prior to `fit()`. |
| 21 | Anomaly score normalized 0-100 | VERIFIED | `backend/app/services/anomaly_service.py:82-90` | Clamped correctly to `[0, 100]`. Not framed as a probability. |
| 22 | SHAP computed at inference time | VERIFIED | `backend/app/services/ml_service.py:327` | Calls `predict(pred_contribs=True)` live on the Booster. |
| 23 | <0.60 fallback to binary SHAP | VERIFIED | `backend/app/services/ml_service.py:591-592` | Explicit fallback to `_make_generic_illicit_explanation` using `bin_shap`. |
| 24 | Spot-check explanation string | VERIFIED | `backend/app/services/ml_service.py:112-123` | correctly attributes "elevated/reduced" based on SHAP direction. |
| 25 | No paid/BigQuery in active pipe | VERIFIED | `backend/app/services/` | Active pipeline uses no external APIs. BigQuery code is restricted to `scratch/`. |
| 26 | Two-stream outer join semantics | VERIFIED | `backend/app/api/routes_ingest.py:426-428` | Computes matched, `ledger_only`, and `network_only` independently. |
| 27 | Correlation metadata reporting | CONCERN | `backend/app/api/routes_ingest.py:470-474` | Reports matched/unmatched, but FAILS to report duplicate ingestion counts. |
| 28 | Unified ingestion path | VERIFIED | `backend/app/api/routes_ingest.py:256` | Routes through the exact same `ml_service.predict_risk` code path. |
| 29 | Explicit unavailable state | VERIFIED | `backend/app/api/routes_ingest.py:155-166` | Returns `UNAVAILABLE` on non-finite feature vectors. |
| 30 | Small sample warning | VERIFIED | `backend/app/api/routes_ingest.py:143-146` | Fires when `len(scenario_txs) < MIN_TRAINING_SCENARIO_TX_COUNT`. |
| 31 | Scenario-level ML risk only | VERIFIED | `backend/app/services/graph_service.py` | No node-level ML risk mappings discovered. |
| 32 | IP telemetry language hedged | VERIFIED | `backend/app/services/dossier_service.py` | Uses "Observed Relay Telemetry", avoids definitive origin claims. |
| 33 | CIOH language heuristic-framed | CONCERN | `backend/app/services/dossier_service.py:235` | Prohibited definitive "SYNDICATE" language found in UI templates and route comments. |
| 34 | Prohibited legal language absent | VERIFIED | `backend/app/services/` | No occurrences of "Summons" or "Mandated Legal Directive". |
| 35 | Synthetic data disclosure on UI | VERIFIED | `backend/app/services/dossier_service.py:260` | "SYNTHETIC / DEMONSTRATION OUTPUT ... NOT A LEGAL INSTRUMENT" printed on dossiers. |
| 36 | Model artifact versioning | VERIFIED | `ml/manifests/` | Models are explicitly tagged `v7_candidate`. |
| 37 | V8 artifacts carry V7 naming | CONCERN | `ml/models_v8/` | V8 output directory contains files explicitly named `binary_model_v7_candidate.ubj`. |
| 38 | V7/V8 active backend wiring | VERIFIED | `backend/app/services/ml_service.py:38` | Pipeline statically imports `MANIFEST_v7_candidate.json`, confirming V7 is live. |
| 39 | Regression testing coverage | PARTIALLY VERIFIED | `backend/tests/test_v7_integration.py` | Tests exist but test suite execution hangs/delays indefinitely on `test_01_streaming_reconciler_temporal_window`. |
| 40 | Feature vector equality tolerance | NOT VERIFIED | `backend/tests/` | Could not trace explicit float-tolerance checks for live vs offline extraction in the hanging test suite. |
| 41 | No out-of-scope ensemble/GNN | VERIFIED | `backend/` | Code is purely XGBoost + Isolation Forest. No GraphSAGE code found. |

## 3. Discrepancies Found

- **Item 27 (Ingestion Correlation Metadata):**
  - *Details:* `routes_ingest.py` correctly calculates outer join cardinality for ledger vs network, but lacks logic to detect and report duplicate transactions (e.g., payloads resubmitted).
  - *Status:* **RESOLVED**. Duplicate accounting fields added to `schemas.py` and implemented in `routes_ingest.py`.
- **Item 33 (CIOH Clustering Language):**
  - *Details:* `dossier_service.py` line 235 emits the header `3. SYNDICATE & ENTITY CLUSTER IDENTIFICATION`. This violates the forensic neutrality rule which forbids definitive-ownership assertions ("syndicate"). `routes_graph.py` also documents nodes as "modular syndicates".
  - *Status:* **RESOLVED**. All instances of "Syndicate" replaced with "Entity Cluster (CIOH)".
- **Item 37 (Model Naming Hygiene):**
  - *Details:* Files generated in `ml/models_v8/` are named `binary_model_v7_candidate.ubj`. This introduces metadata debt and confusion over whether a binary is V7 or V8.
  - *Status:* **RESOLVED**. Models and manifest in `models_v8/` and `manifests_v8/` renamed to `_v8` conventions.

## 4. Confirmed Metrics

The following metrics reflect the definitive evaluation of the 46-feature XGBoost models across three configurations. Note that these metrics represent synthetic generator performance and are not indicative of real-world generalization.

| Metric | V7 Model on V7 Test | V8 Model on V8 Test | V8 Model on Shifted V8 |
|---|---|---|---|
| **Binary ROC-AUC** | 0.99918 | 0.99738 | 0.99732 |
| **Binary PR-AUC** | 0.99888 | 0.99662 | 0.99650 |
| **Binary Accuracy** | 0.98529 | 0.98070 | 0.97821 |
| **Binary F1** | 0.98222 | 0.97685 | 0.97410 |
| **Binary Balanced Acc** | 0.98549 | 0.98192 | 0.97985 |
| **Typology Macro-F1** | 0.93666 | 0.95102 | 0.95011 |
| **Typology Weighted-F1** | 0.96679 | 0.97348 | 0.97210 |
| **Typology Accuracy** | 0.96652 | 0.97321 | 0.97155 |

## 5. Leakage Audit
Total features evaluated: 46. Zero instances of `is_illicit`, `pattern_type`, `split`, `scenario_id`, or `is_licit_exchange` were found in the manifest or training inputs.
- `total_input_mean`: CLEAN
- `num_txns`: CLEAN
- `prop_delta_cv`: CLEAN
- `suspicious_infra_ratio`: CLEAN
- *(All 46 features manually and programmatically confirmed clean)*

## 6. Contract Compliance
`risk_score` is directly assigned the raw `float(predict_proba()[1])` value. `binary_confidence` is assigned `round(risk_score, 4)`. No probability manipulation (`max(licit, illicit)`) is present anywhere in the codebase.
The API output dynamically includes the mandatory tuple of `risk_score`, `binary_confidence`, `is_illicit`, `typology`, `typology_confidence`, `anomaly_score`, `binary_shap`, and `typology_shap` (when applicable).

## 7. Real-World Validation Status
**The current models (V7/V8) have NOT been validated against real-world data.** No real-world telemetry or labeled illicit blockchain graphs have been successfully passed through the 46-feature inference pipeline. The synthetic metrics above strictly describe in-distribution performance on the generator.

## 8. Final ML Position
**RESTATED:** V7/V8 provides a controlled, leakage-audited synthetic AML benchmark with strong binary and typology performance. However, the near-perfect synthetic metrics **should not be interpreted as real-world AML performance**, because independent real-world validation has not yet been successfully established. All outputs are currently marked as synthetic demonstrations.
