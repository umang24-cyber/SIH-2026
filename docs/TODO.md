# Project Task Tracker & Roadmap — SIH PS146

> **Team Responsibilities:**
> - **P1, P2:** Frontend & Dashboard Visualizer
> - **P3:** Data Engineering (Dataset v2.0 Finalized)
> - **P4:** Graph Construction & Typology Heuristics
> - **P5:** ML Feature Engineering, Model Training & Explainability
> - **P6:** Team Lead, Backend API, Database, Offline Linux Integration

---

## 1. Data Engineering (P3)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [x] | Generate master dataset with multi-I/O UTXO array structures | P3 | High | Completed in v2.0 (82,078 transactions) |
| [x] | Synthesize P2P network telemetry with decorrelated reference pools | P3 | High | Completed in v2.0 (15 ASNs, 6 node types) |
| [x] | Inject 30 hard-negative high-activity licit exchange clusters | P3 | High | Completed in v2.0 (9,992 transactions) |
| [x] | Pre-split deterministic 80/20 train/test scenario stratified sets | P3 | High | Zero scenario leakage across 17,613 scenarios |
| [x] | Run and pass 15/15 integrity checks via `validate_v2.py` | P3 | High | 100% integrity validation passed |
| [x] | Maintain schema source of truth in `DATA_DICTIONARY.md` | P3 | High | v2.0 finalized |

---

## 2. Graph Construction & Typology Detection (P4)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [ ] | Implement heterogeneous graph builder (Wallet, Transaction, IP nodes) in NetworkX | P4 | High | Schema per `DATA_DICTIONARY.md` Section 7 |
| [ ] | Add graph edge constructors (`SENT`, `RECEIVED`, `BROADCAST`) with BTC amounts and telemetry | P4 | High | Parse JSON arrays for 1-to-many / many-to-1 links |
| [ ] | Implement `peeling_chain` detection heuristic (1→2 outputs, change address reuse chain traversal) | P4 | High | Per `DATA_DICTIONARY.md` Section 7c |
| [ ] | Implement `layering` detection heuristic (fan-out N outputs followed by fan-in N inputs reconvergence) | P4 | High | Detect split-and-merge laundering structures |
| [ ] | Implement `mixing` detection heuristic (N→N equal-value outputs, multi-round CoinJoin detection via Louvain/Leiden) | P4 | High | Partition equal-denomination subgraphs |
| [ ] | Graph export serializer matching `/graph/{scenario_id}` in `API_CONTRACT.md` | P4 | High | Align early with P1/P2 frontend schema |

---

## 3. Machine Learning & Explainability (P5)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [ ] | Hard-exclude `is_illicit`, `pattern_type`, `scenario_id`, `split` from feature matrix | P5 | Critical | Add automated unit test assertion in `test_ml_safety.py` |
| [ ] | Implement feature engineering pipeline (amounts, fee ratio, `propagation_delta_ms`, one-hot network metadata) | P5 | High | Per `DATA_DICTIONARY.md` Section 8a |
| [ ] | Set up group-aware cross-validation using `scenario_id` (GroupKFold) on `train_*.csv` | P5 | High | Prevent intra-cluster data leakage |
| [ ] | Handle class imbalance for typologies (`peeling_chain`=309, `layering`=123, `mixing`=90 vs `ransomware`=29,545, `normal`=52,011) | P5 | High | Evaluate SMOTE / focal loss / class weighting before multiclass training |
| [ ] | Train LightGBM / XGBoost multi-class and binary classification models | P5 | High | Optimize F1-Score on illicit minority typologies |
| [ ] | Integrate SHAP TreeExplainer for per-prediction local feature attribution generation | P5 | High | Feed into `/alerts/{id}/evidence` endpoint |

---

## 4. Backend & Database Engineering (P6)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [ ] | Set up project repository skeleton and virtual environment | P6 | High | In progress |
| [ ] | Finalize database choice for offline prototype (SQLite vs PostgreSQL) | P6 | Medium | TODO: P6 decision |
| [ ] | Implement CSV data ingestion script with JSON array parsing | P6 | High | Join `blockchain_transactions.csv` + `network_metadata.csv` on `txid` |
| [ ] | Build FastAPI application serving all endpoints defined in `API_CONTRACT.md` | P6 | High | `/entity`, `/transaction`, `/graph`, `/alerts`, `/alerts/{id}/evidence` |
| [ ] | Implement alert ranking engine merging P4 heuristics and P5 ML predictions | P6 | High | Rank by confidence score and severity |
| [ ] | Verify official PS146 PDF from SIH portal for AI/ML Focus Areas table (common-input-ownership clustering, seed-based risk propagation) | P6 | High | Confirm before Phase 2 detection work is finalized |

---

## 5. Frontend & UI Visualizer (P1, P2)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [ ] | Build investigation dashboard layout against mocked alert data shaped like `API_CONTRACT.md` | P1 | High | Do not block on backend completion |
| [ ] | Implement ranked alert triage table with severity badges and filters | P1 | High | Filter by pattern_type, confidence, timestamp |
| [ ] | Build interactive link-analysis graph viewer using Cytoscape.js / vis.js | P2 | High | Render Wallet, Transaction, and IP nodes with custom styling |
| [ ] | Implement forensic evidence drawer showing SHAP feature attributions and telemetry card | P1/P2 | High | Display dual on-chain + network metadata view |
| [ ] | Create presentation deck (PPT) highlighting forensic capabilities and SIH PS146 alignment | P1/P2 | Medium | For competition judging rounds |

---

## 6. Integration & Offline Packaging (P6)

| Status | Task | Owner | Priority | Notes |
|:---:|---|:---:|:---:|---|
| [ ] | Package offline Linux dependencies (wheel files / offline pip cache for WSL2 Ubuntu 24.04) | P6 | High | Ensure 100% offline air-gapped runnability |
| [ ] | Create end-to-end launch script (`run_system.sh` / `start_dev.bat`) | P6 | Medium | Launch backend FastAPI + frontend dev server |
| [ ] | End-to-end integration test: CSV ingestion → graph → ML inference → API → UI visualizer | P6 | High | Validate data integrity across entire stack |
