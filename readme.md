<<<<<<< HEAD
# SIH PS146: AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

[![Target OS: Linux / WSL2](https://img.shields.io/badge/OS-Ubuntu%2024.04%20LTS-E95420?logo=ubuntu&logoColor=white)](file:///c:/Users/arora/SIH/SIH-2026/docs/SETUP.md)
[![Data Schema: v2.0 Finalized](https://img.shields.io/badge/Data%20Schema-v2.0%20(82%2C078%20txns)-blue)](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md)
[![Integrity Checks: 15/15 PASS](https://img.shields.io/badge/Integrity%20Checks-15%2F15%20PASS-brightgreen)](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md#6-join--integrity-validation-report)
[![Zero Leakage Invariant](https://img.shields.io/badge/System%20Invariant-Zero%20Label%20Leakage-success)](file:///c:/Users/arora/SIH/SIH-2026/docs/ARCHITECTURE.md#2-critical-system-invariant-zero-label-leakage)

An offline, air-gapped forensic intelligence and graph-analytics platform designed for law enforcement agencies (LEAs) and Financial Intelligence Units (FIUs) for **Smart India Hackathon (SIH Problem Statement PS146)**. The system continuously ingests dual-layer Bitcoin network telemetry (on-chain multi-input/multi-output UTXO ledgers fused with P2P broadcast network metadata), constructs a multi-entity transaction graph (`Wallet`, `Transaction`, and `IP` nodes), identifies complex money-laundering typologies (`peeling_chain`, `layering`, `mixing`) and ransomware campaigns, classifies candidate illicit structures using trained machine learning models, and outputs ranked, explainable forensic alerts with human-readable reasoning to an interactive link-analysis dashboard.

---

## Table of Contents
1. [Key Capabilities & Innovation](#key-capabilities--innovation)
2. [End-to-End Pipeline Architecture](#end-to-end-pipeline-architecture)
3. [Core Technical Pillars](#core-technical-pillars)
   - [3.1 Dual-Layer Telemetry Ingestion](#31-dual-layer-telemetry-ingestion)
   - [3.2 Multi-Entity Graph Construction](#32-multi-entity-graph-construction)
   - [3.3 Topological Typology Detection](#33-topological-typology-detection)
   - [3.4 Machine Learning & SHAP Explainability](#34-machine-learning--shap-explainability)
   - [3.5 REST Backend & Forensic Evidence Delivery](#35-rest-backend--forensic-evidence-delivery)
   - [3.6 Forensic Investigation Dashboard & CLI](#36-forensic-investigation-dashboard--cli)
4. [Dataset & Data Engineering Summary (v2.0)](#dataset--data-engineering-summary-v20)
5. [Critical System Invariant: Zero Label Leakage](#critical-system-invariant-zero-label-leakage)
6. [API Contract Summary](#api-contract-summary)
7. [Technology Stack](#technology-stack)
8. [Team Roles & Ownership Matrix](#team-roles--ownership-matrix)
9. [Quickstart & Installation Guide](#quickstart--installation-guide)
10. [Documentation Sitemap](#documentation-sitemap)

---

## 1. Key Capabilities & Innovation

- **Dual-Layer Forensic Fusion:** Fuses on-chain financial ledgers (UTXO inputs, outputs, fee rates, script types) with pre-confirmation P2P network telemetry (origin IPv4, Autonomous System Numbers, ISP infrastructure, node classification, broadcast latency).
- **Heterogeneous Graph Engine:** Bipartite link-analysis connecting `Wallet` nodes, multi-I/O `Transaction` nodes, and `IP` broadcast nodes via `SENT`, `RECEIVED`, and `BROADCAST` relationships.
- **Structural Laundering Detectors:** Native graph algorithms for peeling chain traversal (change-address reuse), layering fan-out/fan-in reconvergence, and CoinJoin mixing community detection (Louvain/Leiden modularity).
- **Zero-Leakage ML Classifier:** LightGBM and XGBoost classifiers trained strictly without ground-truth targets or group keys, validated via group-aware `scenario_id` stratification (`GroupKFold`).
- **Forensic Explainability (TreeSHAP):** Every alert generates an exact breakdown of risk-increasing and risk-decreasing feature attributions, synthesizing human-readable evidence summaries for court admissibility.
- **100% Offline & Air-Gapped Operation:** Self-contained architecture running locally on Ubuntu 24.04 LTS / WSL2 with pre-resolved GeoIP telemetry and zero runtime external network calls.

---

## 2. End-to-End Pipeline Architecture

```text
+-------------------------------------------------------------------------------------------------------------------+
|                                                 RAW DATA LAYER                                                    |
|                                                                                                                   |
|   data/processed/blockchain_transactions.csv                  data/processed/network_metadata.csv                 |
|   (82,078 rows · Multi-I/O JSON arrays · BTC Fees)            (82,078 rows · P2P Timestamps · IP/ASN Telemetry)   |
+---------------------------------------------------------+---------------------------------------------------------+
                                                          |
                                                          | 1:1 Inner Join on `txid` (Primary Key)
                                                          v
+-------------------------------------------------------------------------------------------------------------------+
|                                        INGESTION & DATA INTEGRITY LAYER (P6)                                      |
|   - Deserialize JSON array columns (`input_addresses`, `output_addresses`, `input_amounts`, `output_amounts`)     |
|   - Compute propagation latency: `propagation_delta_ms = (timestamp - relay_timestamp)`                           |
|   - Verify 15/15 integrity constraints (Accounting balance: sum(in) = sum(out) + fee)                             |
+-------------------------------------+---------------------------------------------------+-------------------------+
                                      |                                                   |
                                      | Transaction Topology                              | Feature Columns
                                      v                                                   v
+-----------------------------------------------------+   +---------------------------------------------------------+
|           GRAPH ENGINE & TYPOLOGIES (P4)            |   |           FEATURE EXTRACTION & ML ENGINE (P5)           |
|                                                     |   |                                                         |
|   Heterogeneous Graph Nodes:                        |   |   Safe Features Extracted:                              |
|   - Wallet (address, is_licit_exchange)             |   |   - Financial: total_in, total_out, fee_ratio, num_I/O  |
|   - Transaction (txid, timestamp, fee_btc, etc.)    |   |   - Script: P2PKH, P2SH, P2WPKH, P2WSH one-hot          |
|   - IP (relay_ip, country, asn, isp, node_type)      |   |   - Timing: propagation_delta_ms, hour, day-of-week     |
|                                                     |   |   - Network: node_type, high-risk ASN, country freq    |
|   Edge Relationships:                               |   |   - Graph Metrics: in/out degrees, PageRank score       |
|   - SENT (Wallet -> Tx, amount_btc)                 |   |                                                         |
|   - RECEIVED (Tx -> Wallet, amount_btc)             |   |   Validation Strategy: scenario_id GroupKFold (5-Fold)  |
|   - BROADCAST (IP -> Tx, relay_timestamp, port)     |   |   Model: XGBoost / LightGBM Multiclass Classifier       |
|                                                     |   |   Explainability: TreeSHAP Feature Attributions         |
|   Typology Detectors:                               |   |                                                         |
|   - peeling_chain (1->2 out, change-reuse chains)   |   |   * HARD RULE: is_illicit & pattern_type EXCLUDED       |
|   - layering (fan-out N then fan-in N reconvergence)|   |                                                         |
|   - mixing (N->N equal-value multi-round CoinJoin)  |   |                                                         |
+-------------------------------------+---------------+   +---------------------------+-----------------------------+
                                      |                                               |
                                      | Flagged Candidate Subgraphs                   | Risk Probabilities & SHAP
                                      +-----------------------+-----------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                          ALERT & RANKING ENGINE (P5, P6)                                          |
|   - Correlate candidate subgraphs with ML model confidence scores                                                 |
|   - Prioritize alerts: Severity = f(ML Confidence, Typology Structure, Infrastructure Risk)                       |
|   - Synthesize court-ready forensic justification summaries                                                      |
+-------------------------------------------------------------+-----------------------------------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                             FASTAPI REST BACKEND (P6)                                             |
|   - GET /entity/{address}          GET /transaction/{txid}          GET /graph/{scenario_id}                      |
|   - GET /alerts                    GET /alerts/{candidate_id}/evidence                            |
+-------------------------------------------------------------+-----------------------------------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                         INVESTIGATION DASHBOARD (P1, P2)                                          |
|   - Interactive Link Analysis Network Canvas (Cytoscape.js / vis.js / Three.js 3D Force Graph)                    |
|   - Ranked Alert Feed, Live Entity Inspector, SHAP Attribution Waterfall, and Exportable Dossiers                |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Core Technical Pillars

### 3.1 Dual-Layer Telemetry Ingestion
Bitcoin transactions are broadcast to the peer-to-peer mempool seconds to minutes before inclusion in a mined block. Combining P2P broadcast telemetry (`network_metadata.csv`) with the blockchain ledger (`blockchain_transactions.csv`) exposes critical forensic signals:
- **Propagation Delta ($\Delta t$):** $\Delta t = \text{timestamp}_{\text{block}} - \text{timestamp}_{\text{relay}}$. Anomalous propagation latencies distinguish automated syndicate broadcasting from standard wallet clients.
- **Infrastructure Classification:** Peer relay categorization (`residential`, `datacenter`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`, `mobile`) mapped to Autonomous System Numbers (ASNs) and ISPs.

### 3.2 Multi-Entity Graph Construction
Rather than reducing Bitcoin transactions to simple address-to-address links, the graph engine constructs a heterogeneous directed graph per Section 7 of `DATA_DICTIONARY.md`:
- **Nodes:**
  - `Wallet` Node: Keyed by Base58 `address`. Holds `is_licit_exchange` flag.
  - `Transaction` Node: Keyed by 64-bit integer `txid`. Holds `timestamp`, `fee_btc`, `script_type`, and `scenario_id`.
  - `IP` Node: Keyed by IPv4 `relay_ip`. Holds `country_code`, `asn`, `isp`, `node_type`, and `relay_port`.
- **Edges:**
  - `SENT`: Directed edge from `Wallet` $\rightarrow$ `Transaction` with `amount_btc`.
  - `RECEIVED`: Directed edge from `Transaction` $\rightarrow$ `Wallet` with `amount_btc`.
  - `BROADCAST`: Directed edge from `IP` $\rightarrow$ `Transaction` with `relay_timestamp`, `relay_port`, and `user_agent`.

### 3.3 Topological Typology Detection
Dedicated graph heuristics identify the structural hallmarks of complex money laundering:
1. **Peeling Chains (`peeling_chain`):** Traverses long linear sequences of 1-input $\rightarrow$ 2-output transactions where small payments are peeled off while the remaining balance (change output) is repeatedly forwarded to fresh addresses across $\ge 3$ consecutive hops.
2. **Layering (`layering`):** Identifies rapid fund dispersion from 1 source UTXO into $N$ intermediary addresses (Fan-Out), followed by reconvergence of those $N$ streams into a single consolidation address (Fan-In) within a constrained time horizon.
3. **Mixing / CoinJoin (`mixing`):** Evaluates multi-party equal-denomination transactions ($N \text{ in} \rightarrow N \text{ out}$) and uses Louvain/Leiden modularity clustering to identify coordinated anonymization pools.

### 3.4 Machine Learning & SHAP Explainability
- **Feature Set:** Financial statistics (`total_input_btc`, `total_output_btc`, `fee_ratio`, `num_inputs`, `num_outputs`), script type one-hot encodings, timing metrics (`propagation_delta_ms`), network infrastructure categories, and graph centrality scores (`in_degree`, `out_degree`, `pagerank`).
- **Validation Protocol:** Models are evaluated strictly on the 80/20 scenario-stratified pre-split datasets (`train_*.csv` and `test_*.csv`). 5-fold cross-validation is grouped on `scenario_id` to guarantee zero intra-cluster data leakage.
- **Explainability:** SHAP (SHapley Additive exPlanations) computes exact local feature contributions for every flagged candidate, explaining *why* a transaction cluster was marked as suspicious.

### 3.5 REST Backend & Forensic Evidence Delivery
High-performance asynchronous FastAPI service layer exposing endpoints defined in `API_CONTRACT.md`. Provides sub-50ms query responses for scenario subgraphs, entity profiles, ranked alert queues, and multi-hop trace paths.

### 3.6 Forensic Investigation Dashboard & CLI
- **Link-Analysis Canvas:** Interactive visualization rendering multi-hop transaction flows, wallet clusters, and infrastructure nodes.
- **Triage Inbox & Evidence Drawer:** Displays prioritized alerts, interactive SHAP attribution charts, and dual-layer transaction comparisons.
- **Terminal CLI Interface ("BitKaun?"):** Integrated command-line console supporting real-time forensic syscalls (`graph`, `inspect <id>`, `trace <src> <dst>`, `dmesg`, `status`, `help`).

---

## 4. Dataset & Data Engineering Summary (v2.0)

The underlying dataset is generated and validated under **v2.0 specifications**, addressing all limitations of legacy scalar datasets:

| Metric / Dimension | Specification (v2.0 Finalized) | Details & Integrity |
|---|---|---|
| **Total Transactions** | `82,078` rows | 100% 1:1 row alignment between blockchain ledger and network telemetry |
| **Licit / Illicit Split** | `52,011` Licit (63.4%) / `30,067` Illicit (36.6%) | Realistic class distribution spanning 2011 to 2018 |
| **Planted Typologies** | 5 distinct categories | `normal` (52,011), `ransomware` (29,545), `peeling_chain` (309), `layering` (123), `mixing` (90) |
| **UTXO Structure** | Real Multi-I/O Arrays | `input_addresses[]`, `output_addresses[]`, `input_amounts[]`, `output_amounts[]` (JSON strings) |
| **Accounting Identity** | Exact balance match | `sum(input_amounts) = sum(output_amounts) + fee_btc` (0.00000000 residual) |
| **Hard Negatives** | 30 synthetic exchange clusters | 9,992 transactions across high-activity licit exchange wallets to prevent volume shortcuts |
| **Network Decorrelation** | Realistic infrastructure overlap | 14.9% of licit transactions use VPN/Tor; 19.7% of illicit transactions use residential IPs |
| **Scenario Splitting** | Group-Stratified 80/20 | 17,613 total scenarios; zero scenario overlap between `train` (65,659 rows) and `test` (16,419 rows) |
| **Integrity Tests** | **15/15 PASS** | Validated via `data_pipeline/validate_v2.py` |

---

## 5. Critical System Invariant: Zero Label Leakage

> ### ⚠️ SYSTEM ARCHITECTURAL INVARIANT
> The ground-truth columns **`is_illicit`** and **`pattern_type`** MUST NEVER be used as features, inputs, or heuristics during:
> 1. Graph construction algorithms
> 2. Typology detection heuristics (`peeling_chain`, `layering`, `mixing`)
> 3. Machine learning feature extraction matrices or model inference
> 4. Alert ranking heuristics
>
> **Permitted Usage:** `is_illicit` and `pattern_type` flow **ONLY** into offline model evaluation scripts (precision, recall, ROC-AUC, F1-score) to evaluate model efficacy.

---

## 6. API Contract Summary

All endpoints conform strictly to [docs/API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md):

| Method | Endpoint | Primary Use Case | Output Structure |
|---|---|---|---|
| `GET` | `/entity/{address}` | Wallet Profile & Exchange Tag | `address`, `is_licit_exchange`, `total_received_btc`, `total_sent_btc`, `tx_count`, `associated_scenarios` |
| `GET` | `/transaction/{txid}` | Full Dual-Layer Transaction Detail | On-chain arrays (`input_addresses`, `output_amounts`, `fee_btc`, `script_type`) + Network telemetry (`relay_ip`, `asn`, `isp`, `node_type`, `propagation_delta_ms`) |
| `GET` | `/graph/{scenario_id}` | Scenario Subgraph for Visualizer | Heterogeneous array of `nodes` (`Wallet`, `Transaction`, `IP`) and `edges` (`SENT`, `RECEIVED`, `BROADCAST`) |
| `GET` | `/alerts` | Prioritized Investigation Feed | List of ranked alerts with `candidate_id`, `predicted_pattern_type`, `confidence`, `severity`, `explanation`, `member_txids` |
| `GET` | `/alerts/{candidate_id}/evidence` | Forensic Case Dossier | Detailed evidence breakdown, typology heuristic metrics, SHAP feature attributions, and transaction telemetry |

---

## 7. Technology Stack

| Domain | Technologies | Purpose in System |
|---|---|---|
| **Data Ingestion & Validation** | Python 3.11+, Pandas, NumPy, JSON | CSV streaming, JSON array parsing, join operations, integrity testing |
| **Graph Construction & Analysis** | NetworkX, Neo4j (Evaluation) | Multi-entity graph modeling, shortest-path traversal, Louvain community detection |
| **Machine Learning & XAI** | Scikit-Learn, LightGBM, XGBoost, SHAP | Dual-layer feature extraction, group cross-validation, tree classification, SHAP explanations |
| **Backend & REST Services** | FastAPI, Uvicorn, SQLite / PostgreSQL, Pydantic | Asynchronous REST APIs, graph serialization, query filtering, database persistence |
| **Frontend & Visualization** | React, TypeScript, Vite, Cytoscape.js, Three.js WebGL | Interactive link-analysis, ranked alert triage, dual-layer evidence viewer, 3D force graph |
| **Audio Synthesis & FX** | Web Audio API | Procedural retro mechanical keyboard clicks and kernel alert chirps |
| **Target OS & Deployment** | Ubuntu 24.04 LTS (WSL2 / Linux Air-Gapped) | Target deployment and evaluation environment |

---

## 8. Team Roles & Ownership Matrix

| Member | Designated Role | Module Ownership & Primary Deliverables |
|---|---|---|
| **P1** | Frontend Developer | Dashboard UI, Alert Triage interface, Presentation slide deck (PPT) |
| **P2** | Frontend & Visuals | Cytoscape.js / vis.js graph visualization, evidence view, PPT |
| **P3** | Data Engineering | Dataset generation, schema definition, integrity testing (`DATA_DICTIONARY.md` owner) |
| **P4** | Graph Engineering | Multi-entity graph construction, topological typology detection (`peeling_chain`, `layering`, `mixing`) |
| **P5** | ML & Explainability | Feature engineering, XGBoost/LightGBM model training, SHAP explainability engine |
| **P6** | Team Lead & Backend | Architecture integration, FastAPI backend, DB setup, offline Linux / WSL2 packaging |

---

## 9. Quickstart & Installation Guide

### Prerequisites
- Ubuntu 24.04 LTS (Native Linux or Windows WSL2)
- Python 3.11 or 3.12
- Node.js 20.x+ and npm 10.x+

### Step 1: Clone Repository & Set Up Virtual Environment
```bash
# Navigate to repository
cd /path/to/SIH-2026

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: .\venv\Scripts\activate
```

### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*(Dependencies: `pandas`, `numpy`, `networkx`, `scikit-learn`, `xgboost`, `lightgbm`, `shap`, `fastapi`, `uvicorn`, `pydantic`, `pytest`)*

### Step 3: Verify Dataset Integrity
```bash
python data_pipeline/validate_v2.py
```
*Confirms all 15 integrity checks pass across 82,078 transactions with zero scenario leakage.*

### Step 4: Launch Frontend Development Server
```bash
npm install
npm run dev
```
*Access the interactive forensic dashboard at `http://localhost:5173`.*

---

## 10. Documentation Sitemap

- [Data Dictionary & Schema (Source of Truth): DATA_DICTIONARY.md](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md)
- [REST API Contract: docs/API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)
- [System Architecture: docs/ARCHITECTURE.md](file:///c:/Users/arora/SIH/SIH-2026/docs/ARCHITECTURE.md)
- [Frontend Audit & Schema Reconciliation: docs/FRONTEND_AUDIT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/FRONTEND_AUDIT.md)
- [Task Tracking & Roadmap: docs/TODO.md](file:///c:/Users/arora/SIH/SIH-2026/docs/TODO.md)
- [Environment Setup & WSL2 Guide: docs/SETUP.md](file:///c:/Users/arora/SIH/SIH-2026/docs/SETUP.md)
- [Project Changelog: docs/CHANGELOG.md](file:///c:/Users/arora/SIH/SIH-2026/docs/CHANGELOG.md)
- [Backend Specification: docs/backend/BACKEND.md](file:///c:/Users/arora/SIH/SIH-2026/docs/backend/BACKEND.md)
- [Graph Construction & Typologies: docs/graph_ml/GRAPH.md](file:///c:/Users/arora/SIH/SIH-2026/docs/graph_ml/GRAPH.md)
- [Machine Learning & Explainability: docs/graph_ml/ML.md](file:///c:/Users/arora/SIH/SIH-2026/docs/graph_ml/ML.md)
- [Frontend Dashboard & Visualizer: docs/frontend/FRONTEND.md](file:///c:/Users/arora/SIH/SIH-2026/docs/frontend/FRONTEND.md)
=======
# Bitcoin AML Synthetic Dataset (SIH PS 146)

## 1. Dataset Purpose
This repository generates and analyzes a highly realistic, synthetic Bitcoin Anti-Money Laundering (AML) dataset. The purpose is to provide a standardized benchmark for testing graph-based machine learning models against complex, decentralized illicit behaviors on the blockchain.

## 2. V6 Generation
The dataset is currently frozen at **Version 6 (V6)**. V6 resolves historical artifacts (such as Licit dense-graph artificially bounded wallets) by implementing an organic, unbounded wallet pool. It incorporates genuine semantic composites (e.g., ransomware campaigns utilizing mixers for cash-out) to ensure structural overlap between licit and illicit typologies without resorting to arbitrary label swapping.

## 3. Data Flow & Feature Engineering
The exact data flow of the production pipeline is:
1. `generate_v6.py` → Raw `blockchain_transactions.csv` & `network_metadata.csv` (V6 FROZEN)
2. `01_eda_and_validation.py` → Split creation & schema validation
3. `02_feature_engineering.py` → Base structural, temporal, amount, and network features
4. `02b_graph_features.py` → Graph Engine features (Centrality, Assortativity, Clustering)
5. `02c_merge_features.py` → Final Train/Test Feature Matrices
6. `train_production.py` → Model Training & Evaluation

## 4. Scenario-Level Splitting & Leakage Prevention
To prevent data leakage, the entire dataset is split into training and testing sets at the **scenario level** rather than the transaction level. There is strictly zero transaction, address, or scenario overlap between the splits. Labels and generator metadata are systematically stripped before the feature matrices reach the ML pipeline.

## 5. Machine Learning Tasks
The ML architecture is divided into two distinct stages:

### Stage 1: Binary Classification
- **Goal:** Classify scenarios as Licit (0) or Illicit (1).
- **Model:** XGBoost Classifier.
- **Results:** The V6 feature space requires non-linear fusion of structural and temporal metrics, successfully preventing shallow depth-2 trees from solving the task (BAcc ~0.80), while allowing a full XGBoost model to achieve exceptional performance (AUC ~0.999).

### Stage 2: Typology Classification
- **Goal:** Classify illicit scenarios into one of four distinct typologies: Ransomware, Peeling Chain, Layering, or Mixing.
- **Model:** Multi-class XGBoost Classifier (illicit scenarios only).
- **Results:** Achieves Macro-F1 = 1.000.

## 6. Revised Acceptance Methodology (Gate I)
The original Gate I methodology ("Top-3 Individual Feature Ablation") was systematically deprecated. Individual-feature ablation is insufficient in a highly correlated graph-theoretic feature space (e.g., ablating `max_chain_length` causes the model to seamlessly substitute `edge_to_node_ratio`). 

V6 is instead validated using **Feature-Group Ablation** and **Structural-Fingerprint Analysis**. By deleting entire families of features (e.g., all Graph features), we proved that the perfect typology classification is a mathematical consequence of legitimate AML behavior shaping the graphs, and not a deterministic generator artifact.

## 7. Feature Groups
Features are divided into six semantic families:
- **Amount**: Flow of funds, fees, output distributions
- **Temporal**: Time span, burstiness, transaction delays
- **Structural**: Inputs/outputs, address reuse, fan-in/fan-out
- **Network**: ASN counts, Suspicious IP ratios
- **Script**: Transaction scripting complexities
- **Graph**: Density, centrality, assortativity (via networkx engine)

## 8. Reproducibility
The complete production ML pipeline is 100% deterministic. To execute the final models and rebuild all evaluation metrics from the frozen V6 processed features:
```bash
conda activate ml
bash run_production_pipeline.sh
```
Results, logs, and `MANIFEST_v6.json` will be safely output to `ml/models`, `ml/reports`, and `ml/manifests`.

## 9. Known Limitations
- The synthetic dataset, while structurally overlapping, is ultimately bounded by the logic defined in the V6 generator.
- Performance in the wild (against real-world blockchain data) may degrade as unmodeled typologies and zero-day mixing services emerge.
- The default binary classification threshold is `0.50`, which provides an ECE of ~0.007. Thresholds should be tuned based on operational False Positive constraints.
>>>>>>> origin/graph
