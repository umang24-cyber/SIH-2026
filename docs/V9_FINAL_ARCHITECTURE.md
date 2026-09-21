# BitKaun V9 Final Application Architecture

## 1. System Overview
BitKaun V9 is an offline, forensic, decision-support machine learning prototype designed for detecting illicit activity on the Bitcoin network. It employs a two-tier evaluation architecture separating structural evidence generation from binary risk scoring. The system surfaces highly suspicious financial patterns natively localized with SHAP feature attributions, enabling analyst investigation.

## 2. Data Flow
1. **Mempool/Graph Extraction:** Pre-defined transactions are materialized into a temporal graph database representing chronological flow.
2. **Feature Construction:** 46 approved global features are extracted for each complete scenario.
3. **ML Evaluation (Scenario Level):** The complete scenario is fed into the V9 XGBoost Binary Model and Typology Classifier.
4. **Alert Generation:** If `risk_score >= 0.50`, the scenario becomes a primary alert.
5. **Evidence Extraction:** For illicit alerts, structural traversal algorithms extract subsets of transactions (e.g., peeling chains, layering subgraphs).
6. **Dossier Compilation:** Structural candidates are appended directly to the parent alert as explanatory localization evidence.

## 3. Scenario-Level ML Scoring
The core operational unit for ML evaluation is the **Complete Scenario**.
Evidence subgraphs, sub-chains, and partial candidates are NEVER passed individually to the ML model for scoring. The binary risk and typology attribution always represent the behavioral likelihood of the full temporal graph associated with the scenario.

## 4. Binary Risk Semantics
- **risk_score (P(illicit))**: The primary signal for alert generation. This is the calibrated probability estimate output by the binary XGBoost model.
- **Ranking**: All alerts are strictly ranked by `risk_score` in descending order.
- **Gate**: The system defaults to a hard threshold of 0.50 to emit an alert to the analyst queue.

## 5. Typology Semantics
- **Typology Confidence**: The probability output from the secondary multi-class XGBoost model (predicting ransomware, layering, mixing, peeling chain, etc.).
- **Purpose**: Typology is treated as supporting attribution / metadata.
- **Independence**: Typology confidence does **not** influence the primary alert risk score or the primary queue ranking.

## 6. Isolation Forest Semantics (Anomaly Score)
- **Definition**: A measure of unusualness (0-100) relative only to the licit training distribution.
- **Role**: This is strictly contextual. It operates exclusively as a deterministic tie-breaker during ranking if two scenarios share an identical risk score (`anomaly_score DESC`).
- **Isolation**: The anomaly score does not act as a probability, and high anomaly scores alone do not promote normal scenarios into the illicit alert queue.

## 7. Evidence Extraction
Structural candidates discovered within a scenario (e.g. nested mixing loops, specific layering funnels) are extracted and embedded directly inside the single parent alert's dossier. These regions serve solely to accelerate manual analyst localization.

## 8. Alert Ranking
The frontend visualizer and backend APIs rank the primary alert list using the following strict deterministic sequence:
1. `risk_score DESC`
2. `anomaly_score DESC`
3. `scenario_id ASC`

Visual groupings (e.g. CRITICAL, HIGH) map exactly to `risk_score` tiers to preserve perfect risk-first alignment.

## 9. API Contract
- `GET /alerts?sort_by=risk_score`: Returns a flattened, deduplicated list of complete scenarios flagged as illicit.
- `GET /alerts/{candidate_id}/evidence`: Returns the deep forensic dossier for a specific scenario, including its temporal transactions, origin telemetry, and extracted evidence regions. Note: `candidate_id` acts as the stable alias for the scenario's alert ID (e.g. `alert_{scenario_id}`).

## 10. Frontend Behavior
The frontend strictly inherits backend ordering. Visual grouping by severity is fully compatible because severity operates as a monotonic transform of `risk_score`. Re-sorting by anomaly or typology confidence is intentionally disabled by default to enforce risk-oriented triage.

## 11. Leakage Safeguards
The frozen V9 test set was evaluated identically exactly once. Scenario and transaction ID intersections between the training set and frozen test are verifiably zero. Forbidden fields (`is_illicit`, `pattern_type`, `scenario_id`, `split`, `is_licit_exchange`) are hard-excluded from inference.

## 12. Synthetic-Data Disclosure
BitKaun V9 models were trained entirely on procedurally generated synthetic behaviors meant to mimic illicit typologies. Real-world structural variations will naturally diverge from synthetic anchors, and the prototype's efficacy on live mainnet traffic is uncalibrated.

## 13. Offline / Data-Sovereignty Design
All models, features, SHAP analyses, and telemetry mapping run natively on the local machine. No external cloud dependencies or API keys are required for inference, preserving absolute data sovereignty.

## 14. Known Limitations
- **Gate A Failure:** The V9 model formally failed the original size-controlled Gate A protocol during frozen evaluation due to over-fitting on structural artifact sizes (transaction counts/volumes) inherent to the generator.
- **Locked Test:** The frozen test remains locked post-evaluation.
- **Not Legal Proof:** This system is an offline decision-support prototype. ML attribution, risk scoring, and node mapping do not constitute proof of criminality, jurisdiction, or identity.

## 15. Demo Instructions
1. Start the services via `bash run_ubuntu.sh` (activates backend on port 8000 and frontend on port 5173).
2. Open the React frontend. The primary list is the active triage queue.
3. Observe the alerts sorted inherently by CRITICAL > HIGH > MEDIUM based purely on risk score.
4. Click `alerts --detail <candidate_id>` to drill into the comprehensive dossier.
5. Inspect the SHAP attributions and the mapped localization evidence without losing the parent scenario context.
