# SIH PS146: AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

## Project Overview

An offline, air-gapped Linux-based forensic intelligence platform designed for law enforcement and financial intelligence units (FIUs). The system ingests dual-layer Bitcoin telemetry (on-chain multi-input/multi-output UTXO ledgers combined with P2P broadcast network metadata), constructs a multi-entity transaction graph (Wallet, Transaction, and IP nodes), detects illicit structural money-laundering typologies (`peeling_chain`, `layering`, `mixing`) and ransomware campaigns, classifies candidate illicit structures using trained machine learning models, and serves ranked, explainable forensic alerts with human-readable reasoning to an interactive link-analysis investigation dashboard.

### Architecture Pipeline

```text
+----------------------------------------------------------------------------------------------------+
|                                      INGESTION & DATA LAYER                                        |
|  data/processed/blockchain_transactions.csv  +  data/processed/network_metadata.csv (Join: txid)   |
+-------------------------------------------------+--------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    GRAPH ENGINE & TYPOLOGIES (P4)                                  |
|  - Nodes: Wallet (address), Transaction (txid), IP (relay_ip)                                      |
|  - Edges: SENT (Wallet->Tx), RECEIVED (Tx->Wallet), BROADCAST (IP->Tx)                             |
|  - Structural Heuristics: Peeling Chain Traversal, Layering Fan-Out/In, Mixing Detection           |
+-------------------------------------------------+--------------------------------------------------+
                                                  | Extracted Candidate Subgraphs
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                    ML CLASSIFIER & SHAP (P5)                                       |
|  - Feature Extraction (Amounts, Script Types, Propagation Delta, Decorrelated Network Metadata)   |
|  - Invariant: is_illicit & pattern_type strictly EXCLUDED from training features                   |
|  - Multiclass / Binary Inference + SHAP Attribution Values                                         |
+-------------------------------------------------+--------------------------------------------------+
                                                  | Ranked Alert Records + Explanations
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                     BACKEND API SERVICE (P6)                                       |
|  - FastAPI REST Layer (API_CONTRACT.md endpoints)                                                  |
|  - Graph Serializer & Forensic Evidence Aggregator                                                |
+-------------------------------------------------+--------------------------------------------------+
                                                  | JSON REST Responses
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                 INVESTIGATION DASHBOARD (P1, P2)                                   |
|  - Link-Analysis Graph Visualizer (Cytoscape.js / vis.js)                                          |
|  - Ranked Alert Feed, Evidence Drawer & Forensic Dossier Export                                    |
+----------------------------------------------------------------------------------------------------+
```

---

## Technology Stack

| Layer | Technologies & Libraries | Purpose |
|---|---|---|
| **Data & Core** | Python 3.11+, Pandas, NumPy, JSON | Data loading, JSON array parsing, join operations, integrity validation |
| **Graph Construction** | NetworkX, Neo4j (Optional / Evaluation) | Heterogeneous graph construction, topological traversal, community detection |
| **Machine Learning & XAI** | Scikit-Learn, XGBoost, LightGBM, SHAP | Dual-layer feature extraction, group cross-validation, tree classification, SHAP explanations |
| **Backend & API** | FastAPI, Uvicorn, SQLite / PostgreSQL, Pydantic | REST API services, sub-graph serialization, query filtering, database persistence |
| **Frontend & UI** | React, TypeScript, Vite, Cytoscape.js / vis.js, Tailwind CSS / Vanilla CSS | Interactive graph link-analysis, ranked alert triage, dual-layer evidence viewer |
| **Target OS / Environment** | Ubuntu 24.04 LTS (WSL2 / Offline Air-Gapped Linux) | Target deployment and evaluation environment |

---

## Team Roles & Ownership

| Member | Role | Core Modules & Responsibilities |
|---|---|---|
| **P1** | Frontend Developer | Dashboard UI, Alert Triage interface, Presentation / PPT |
| **P2** | Frontend & Visuals | Cytoscape.js / vis.js graph visualization, evidence view, PPT |
| **P3** | Data Engineering | Dataset generation, schema definition, integrity testing (`DATA_DICTIONARY.md` owner) |
| **P4** | Graph Engineering | Multi-entity graph construction, topological typology detection (`peeling_chain`, `layering`, `mixing`) |
| **P5** | ML & Explainability | Feature engineering, XGBoost/LightGBM model training, SHAP explainability engine |
| **P6** | Team Lead & Backend | Architecture integration, FastAPI backend, DB setup, offline Linux / WSL2 packaging |

---

## Documentation Index

- [Schema Source of Truth: DATA_DICTIONARY.md](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md) (v2.0 finalized)
- [API Contract: docs/API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)
- [System Architecture: docs/ARCHITECTURE.md](file:///c:/Users/arora/SIH/SIH-2026/docs/ARCHITECTURE.md)
- [Project Changelog: docs/CHANGELOG.md](file:///c:/Users/arora/SIH/SIH-2026/docs/CHANGELOG.md)
- [Task Tracking & TODOs: docs/TODO.md](file:///c:/Users/arora/SIH/SIH-2026/docs/TODO.md)
- [Environment Setup Guide: docs/SETUP.md](file:///c:/Users/arora/SIH/SIH-2026/docs/SETUP.md)
- [Backend Specification: docs/backend/BACKEND.md](file:///c:/Users/arora/SIH/SIH-2026/docs/backend/BACKEND.md)
- [Graph Construction & Typologies: docs/graph_ml/GRAPH.md](file:///c:/Users/arora/SIH/SIH-2026/docs/graph_ml/GRAPH.md)
- [Machine Learning & Explainability: docs/graph_ml/ML.md](file:///c:/Users/arora/SIH/SIH-2026/docs/graph_ml/ML.md)
- [Frontend Dashboard & Visualizer: docs/frontend/FRONTEND.md](file:///c:/Users/arora/SIH/SIH-2026/docs/frontend/FRONTEND.md)
