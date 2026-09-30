# SIH PS146: AI-Powered Monitoring & Analysis of Bitcoin Transaction Traffic

[![Target OS: Linux / WSL2](https://img.shields.io/badge/OS-Ubuntu%2024.04%20LTS-E95420?logo=ubuntu&logoColor=white)](docs/SETUP.md)
[![Data Schema: v2.0 Finalized](https://img.shields.io/badge/Data%20Schema-v2.0%20(82%2C078%20txns)-blue)](DATA_DICTIONARY.md)
[![Integrity Checks: 15/15 PASS](https://img.shields.io/badge/Integrity%20Checks-15%2F15%20PASS-brightgreen)](DATA_DICTIONARY.md#6-join--integrity-validation-report)
[![Zero Leakage Invariant](https://img.shields.io/badge/System%20Invariant-Zero%20Label%20Leakage-success)](docs/ARCHITECTURE.md)

An offline, air-gapped forensic intelligence and graph-analytics platform designed for law enforcement agencies (LEAs) and Financial Intelligence Units (FIUs) for **Smart India Hackathon (SIH Problem Statement PS146)**. The system continuously ingests dual-layer Bitcoin network telemetry (on-chain multi-input/multi-output UTXO ledgers fused with P2P broadcast network metadata), constructs a multi-entity transaction graph (`Wallet`, `Transaction`, and `IP` nodes), identifies complex money-laundering typologies (`peeling_chain`, `layering`, `mixing`) and ransomware campaigns, classifies candidate illicit structures using trained machine learning models, and outputs ranked, explainable forensic alerts with human-readable reasoning to an interactive link-analysis dashboard.

---

## Table of Contents
1. [Key Capabilities & Innovation](#1-key-capabilities--innovation)
2. [End-to-End Pipeline Architecture](#2-end-to-end-pipeline-architecture)
3. [Core Technical Pillars](#3-core-technical-pillars)
   - [3.1 Dual-Layer Telemetry Ingestion](#31-dual-layer-telemetry-ingestion)
   - [3.2 Multi-Entity Graph Construction](#32-multi-entity-graph-construction)
   - [3.3 Topological Typology Detection](#33-topological-typology-detection)
   - [3.4 Machine Learning & SHAP Explainability](#34-machine-learning--shap-explainability)
   - [3.5 REST Backend & Forensic Evidence Delivery](#35-rest-backend--forensic-evidence-delivery)
   - [3.6 Forensic Investigation Dashboard & CLI](#36-forensic-investigation-dashboard--cli)
4. [Dataset & Data Engineering Summary (v2.0)](#4-dataset--data-engineering-summary-v20)
5. [Critical System Invariant: Zero Label Leakage](#5-critical-system-invariant-zero-label-leakage)
6. [API Contract Summary](#6-api-contract-summary)
7. [Technology Stack](#7-technology-stack)
8. [Team Roles & Ownership Matrix](#8-team-roles--ownership-matrix)
9. [Quickstart & Installation Guide](#9-quickstart--installation-guide)
10. [BitKaun CLI Reference](#10-bitkaun-cli-reference)
11. [ML Performance Metrics](#11-ml-performance-metrics)
12. [Documentation Sitemap](#12-documentation-sitemap)

---

## 1. Key Capabilities & Innovation

- **Dual-Layer Forensic Fusion:** Fuses on-chain financial ledgers (UTXO inputs, outputs, fee rates, script types) with pre-confirmation P2P network telemetry (origin IPv4, Autonomous System Numbers, ISP infrastructure, node classification, broadcast latency).
- **Heterogeneous Graph Engine:** Bipartite link-analysis connecting `Wallet` nodes, multi-I/O `Transaction` nodes, and `IP` broadcast nodes via `SENT`, `RECEIVED`, and `BROADCAST` relationships.
- **Structural Laundering Detectors:** Native graph algorithms for peeling chain traversal (change-address reuse), layering fan-out/fan-in reconvergence, and CoinJoin mixing community detection (Louvain/Leiden modularity).
- **Zero-Leakage ML Classifier:** XGBoost classifiers trained strictly without ground-truth targets or group keys, validated via group-aware `scenario_id` stratification (`GroupKFold`).
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
|                                        INGESTION & DATA INTEGRITY LAYER                                           |
|   - Deserialize JSON array columns (`input_addresses`, `output_addresses`, `input_amounts`, `output_amounts`)     |
|   - Compute propagation latency: `propagation_delta_ms = (timestamp - relay_timestamp)`                           |
|   - Verify 15/15 integrity constraints (Accounting balance: sum(in) = sum(out) + fee)                             |
+-------------------------------------+---------------------------------------------------+-------------------------+
                                      |                                                   |
                                      | Transaction Topology                              | Feature Columns
                                      v                                                   v
+-----------------------------------------------------+   +---------------------------------------------------------+
|           GRAPH ENGINE & TYPOLOGIES                 |   |           FEATURE EXTRACTION & ML ENGINE                |
|                                                     |   |                                                         |
|   Heterogeneous Graph Nodes:                        |   |   Safe Features Extracted:                              |
|   - Wallet (address, is_licit_exchange)             |   |   - Financial: total_in, total_out, fee_ratio, num_I/O  |
|   - Transaction (txid, timestamp, fee_btc, etc.)    |   |   - Script: P2PKH, P2SH, P2WPKH, P2WSH one-hot          |
|   - IP (relay_ip, country, asn, isp, node_type)     |   |   - Timing: propagation_delta_ms, hour, day-of-week     |
|                                                     |   |   - Network: node_type, high-risk ASN, country freq     |
|   Edge Relationships:                               |   |   - Graph Metrics: in/out degrees, PageRank score        |
|   - SENT (Wallet -> Tx, amount_btc)                 |   |                                                         |
|   - RECEIVED (Tx -> Wallet, amount_btc)             |   |   Validation: scenario_id GroupKFold (5-Fold)            |
|   - BROADCAST (IP -> Tx, relay_timestamp, port)     |   |   Model: XGBoost Multiclass Classifier                  |
|                                                     |   |   Explainability: TreeSHAP Feature Attributions          |
|   Typology Detectors:                               |   |                                                         |
|   - peeling_chain (1->2 out, change-reuse chains)   |   |   * HARD RULE: is_illicit & pattern_type EXCLUDED        |
|   - layering (fan-out N then fan-in N)              |   |                                                         |
|   - mixing (N->N equal-value CoinJoin)              |   |                                                         |
+-------------------------------------+---------------+   +---------------------------+-----------------------------+
                                      |                                               |
                                      | Flagged Candidate Subgraphs                   | Risk Probabilities & SHAP
                                      +-----------------------+-----------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                          ALERT & RANKING ENGINE                                                   |
|   - Correlate candidate subgraphs with ML model confidence scores                                                 |
|   - Prioritize alerts: Severity = f(ML Confidence, Typology Structure, Infrastructure Risk)                       |
|   - Synthesize court-ready forensic justification summaries                                                       |
+-------------------------------------------------------------+-----------------------------------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                             FASTAPI REST BACKEND                                                  |
|   - GET /entity/{address}          GET /transaction/{txid}          GET /graph/{scenario_id}                      |
|   - GET /alerts                    GET /alerts/{candidate_id}/evidence                                            |
+-------------------------------------------------------------+-----------------------------------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
|                                         INVESTIGATION DASHBOARD & CLI                                             |
|   - Interactive Link Analysis Network Canvas (Cytoscape.js / Three.js 3D Force Graph)                            |
|   - Ranked Alert Feed, Live Entity Inspector, SHAP Attribution Waterfall, and Exportable Dossiers                 |
|   - BitKaun CLI: forensic REPL terminal (graph, inspect, trace, alerts, status)                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Core Technical Pillars

### 3.1 Dual-Layer Telemetry Ingestion
Bitcoin transactions are broadcast to the peer-to-peer mempool seconds to minutes before inclusion in a mined block. Combining P2P broadcast telemetry (`network_metadata.csv`) with the blockchain ledger (`blockchain_transactions.csv`) exposes critical forensic signals:
- **Propagation Delta (Δt):** `Δt = timestamp_block - timestamp_relay`. Anomalous propagation latencies distinguish automated syndicate broadcasting from standard wallet clients.
- **Infrastructure Classification:** Peer relay categorization (`residential`, `datacenter`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`, `mobile`) mapped to Autonomous System Numbers (ASNs) and ISPs.

### 3.2 Multi-Entity Graph Construction
Rather than reducing Bitcoin transactions to simple address-to-address links, the graph engine constructs a heterogeneous directed graph:
- **Nodes:**
  - `Wallet` Node: Keyed by Base58 `address`. Holds `is_licit_exchange` flag.
  - `Transaction` Node: Keyed by 64-bit integer `txid`. Holds `timestamp`, `fee_btc`, `script_type`, and `scenario_id`.
  - `IP` Node: Keyed by IPv4 `relay_ip`. Holds `country_code`, `asn`, `isp`, `node_type`, and `relay_port`.
- **Edges:**
  - `SENT`: Directed edge from `Wallet` → `Transaction` with `amount_btc`.
  - `RECEIVED`: Directed edge from `Transaction` → `Wallet` with `amount_btc`.
  - `BROADCAST`: Directed edge from `IP` → `Transaction` with `relay_timestamp`, `relay_port`, and `user_agent`.

### 3.3 Topological Typology Detection
Dedicated graph heuristics identify the structural hallmarks of complex money laundering:
1. **Peeling Chains (`peeling_chain`):** Traverses long linear sequences of 1-input → 2-output transactions where small payments are peeled off while the remaining balance is repeatedly forwarded to fresh addresses across ≥3 consecutive hops.
2. **Layering (`layering`):** Identifies rapid fund dispersion from 1 source UTXO into N intermediary addresses (Fan-Out), followed by reconvergence into a single consolidation address (Fan-In) within a constrained time horizon.
3. **Mixing / CoinJoin (`mixing`):** Evaluates multi-party equal-denomination transactions (N in → N out) and uses Louvain/Leiden modularity clustering to identify coordinated anonymization pools.

### 3.4 Machine Learning & SHAP Explainability
- **Feature Set:** Financial statistics (`total_input_btc`, `total_output_btc`, `fee_ratio`, `num_inputs`, `num_outputs`), script type one-hot encodings, timing metrics (`propagation_delta_ms`), network infrastructure categories, and graph centrality scores (`in_degree`, `out_degree`, `pagerank`).
- **Validation Protocol:** Models are evaluated strictly on the 80/20 scenario-stratified pre-split datasets (`train_*.csv` and `test_*.csv`). 5-fold cross-validation is grouped on `scenario_id` to guarantee zero intra-cluster data leakage.
- **Explainability:** SHAP (SHapley Additive exPlanations) computes exact local feature contributions for every flagged candidate, explaining *why* a transaction cluster was marked as suspicious.

### 3.5 REST Backend & Forensic Evidence Delivery
High-performance asynchronous FastAPI service layer exposing endpoints defined in `docs/API_CONTRACT.md`. Provides sub-50ms query responses for scenario subgraphs, entity profiles, ranked alert queues, and multi-hop trace paths.

### 3.6 Forensic Investigation Dashboard & CLI
- **Link-Analysis Canvas:** Interactive visualization rendering multi-hop transaction flows, wallet clusters, and infrastructure nodes.
- **Triage Inbox & Evidence Drawer:** Displays prioritized alerts, interactive SHAP attribution charts, and dual-layer transaction comparisons.
- **Terminal CLI Interface ("BitKaun?"):** Integrated command-line console supporting real-time forensic syscalls (`graph`, `inspect <id>`, `trace <src> <dst>`, `alerts`, `status`, `help`).

---

## 4. Dataset & Data Engineering Summary (v2.0)

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

All endpoints conform strictly to [docs/API_CONTRACT.md](docs/API_CONTRACT.md):

| Method | Endpoint | Primary Use Case | Output Structure |
|---|---|---|---|
| `GET` | `/entity/{address}` | Wallet Profile & Exchange Tag | `address`, `is_licit_exchange`, `total_received_btc`, `total_sent_btc`, `tx_count`, `associated_scenarios` |
| `GET` | `/transaction/{txid}` | Full Dual-Layer Transaction Detail | On-chain arrays + Network telemetry (`relay_ip`, `asn`, `isp`, `node_type`, `propagation_delta_ms`) |
| `GET` | `/graph/{scenario_id}` | Scenario Subgraph for Visualizer | Heterogeneous array of `nodes` (`Wallet`, `Transaction`, `IP`) and `edges` (`SENT`, `RECEIVED`, `BROADCAST`) |
| `GET` | `/alerts` | Prioritized Investigation Feed | Ranked alerts with `candidate_id`, `predicted_pattern_type`, `confidence`, `severity`, `explanation` |
| `GET` | `/alerts/{candidate_id}/evidence` | Forensic Case Dossier | Evidence breakdown, typology heuristic metrics, SHAP feature attributions, transaction telemetry |

---

## 7. Technology Stack

| Domain | Technologies | Purpose in System |
|---|---|---|
| **Data Ingestion & Validation** | Python 3.11+, Pandas, NumPy | CSV streaming, JSON array parsing, join operations, integrity testing |
| **Graph Construction & Analysis** | NetworkX | Multi-entity graph modeling, shortest-path traversal, Louvain community detection |
| **Machine Learning & XAI** | Scikit-Learn, XGBoost, SHAP | Feature extraction, group cross-validation, tree classification, SHAP explanations |
| **Backend & REST Services** | FastAPI, Uvicorn, SQLite, Pydantic | Asynchronous REST APIs, graph serialization, query filtering, database persistence |
| **Frontend & Visualization** | React, TypeScript, Vite, Cytoscape.js, Three.js | Interactive link-analysis, ranked alert triage, dual-layer evidence viewer, 3D force graph |
| **CLI** | Python, Rich, Requests | Forensic REPL terminal with phosphor-green UI |
| **Target OS & Deployment** | Ubuntu 24.04 LTS (WSL2 / Linux Air-Gapped) | Target deployment and evaluation environment |

---

## 8. Team Roles & Ownership Matrix

| Member | Designated Role | Module Ownership & Primary Deliverables |
|---|---|---|
| **P1** | Frontend Developer | Dashboard UI, Alert Triage interface, Presentation slide deck (PPT) |
| **P2** | Frontend & Visuals | Cytoscape.js / vis.js graph visualization, evidence view, PPT |
| **P3** | Data Engineering | Dataset generation, schema definition, integrity testing (`DATA_DICTIONARY.md` owner) |
| **P4** | Graph Engineering | Multi-entity graph construction, topological typology detection (`peeling_chain`, `layering`, `mixing`) |
| **P5** | ML & Explainability | Feature engineering, XGBoost model training, SHAP explainability engine |
| **P6** | Team Lead & Backend | Architecture integration, FastAPI backend, DB setup, offline Linux / WSL2 packaging |

---

## 9. Quickstart & Installation Guide

### Prerequisites
- Ubuntu 24.04 LTS (Native Linux or Windows WSL2)
- Python 3.11 or 3.12
- Node.js 20.x+ and npm 10.x+

### Step 1: Clone Repository & Set Up Virtual Environment
```bash
cd SIH-2026

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: .\venv\Scripts\activate
```

### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Verify Dataset Integrity
```bash
python data_pipeline/validate_v2.py
```
*Confirms all 15 integrity checks pass across 82,078 transactions with zero scenario leakage.*

### Step 4: Launch Backend (Terminal 1)
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*FastAPI server starts at `http://localhost:8000`. Verify with: `curl http://localhost:8000/health`*

### Step 5: Launch Frontend Dashboard (Terminal 2)
```bash
npm install
npm run dev
```
*Access the interactive forensic dashboard at `http://localhost:5173`.*

### Step 6: (Optional) Install & Launch BitKaun CLI
```bash
cd cli
pip install -e .
bitkaun        # launches interactive REPL
```

### Windows (Quick Start)
```bat
run_backend.bat    # starts backend on port 8000
```

---

## 10. BitKaun CLI Reference

> **Package:** `bitkaun` · **Backend Target:** `http://localhost:8000` · **100% Offline**

`bitkaun` is a production-grade command-line interface for the BitKaun AML Forensics Platform. Once installed (`pip install -e ./cli`), typing `bitkaun` drops the investigator into a persistent phosphor-green forensic REPL (`bitkaun@investigation:~$ `).

### Commands

| Command | Syntax | Description |
|---|---|---|
| `status` | `status` | Runtime health, transaction count, wallet count, ML model status |
| `inspect` | `inspect <address\|txid>` | Deep forensic inspection of wallet or transaction |
| `graph` | `graph <scenario_id>` | ASCII topology tree + node/edge census for a scenario |
| `trace` | `trace <src_address> <dst_address>` | Multi-hop shortest path between two wallets |
| `alerts` | `alerts [--limit N] [--detail <candidate_id>]` | Ranked alert feed + SHAP evidence dossier |
| `help` | `help [command]` | Command index or syntax for a specific command |
| `clear` | `clear` | Refresh the BitKaun header banner |
| `exit` | `exit` / `quit` | Gracefully exit the REPL session |

### Example Session
```
bitkaun@investigation:~$ status
bitkaun@investigation:~$ graph ransomware_03287
bitkaun@investigation:~$ inspect 187888339
bitkaun@investigation:~$ trace 1jLgHKBTV4wPz8zugRhGrKfs6qcs 1wyjiCSKUZtym1hXSXRPnCgbHi6rhqU
bitkaun@investigation:~$ alerts --detail cand_ransom_ransomware_03287_187888339
```

---

## 11. ML Performance Metrics

The following metrics reflect the definitive evaluation of the 46-feature XGBoost v9 model on the held-out test set. These metrics represent synthetic generator performance.

| Metric | V8 Model on V8 Test | **V9 Model on V9 Test** |
|---|---|---|
| **Binary ROC-AUC** | 0.99738 | **0.99800+** |
| **Binary PR-AUC** | 0.99662 | — |
| **Binary Accuracy** | 0.98070 | — |
| **Binary F1** | 0.97685 | — |
| **Binary Balanced Acc** | 0.98192 | — |
| **Typology Macro-F1** | 0.95102 | — |
| **Typology Weighted-F1** | 0.97348 | — |
| **Typology Accuracy** | 0.97321 | — |

*Full v9 evaluation reports: `ml/reports/binary_metrics_v9.json`, `ml/reports/typology_metrics_v9.json`*

---

## 12. Documentation Sitemap

| Document | Path | Description |
|---|---|---|
| **Data Dictionary** | [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Schema source of truth, field definitions, integrity validation |
| **System Architecture** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Component diagrams, data flow, design decisions |
| **REST API Contract** | [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Endpoint specs, request/response schemas |
| **Full Technical Docs** | [docs/DOCS.md](docs/DOCS.md) | Comprehensive implementation documentation |
| **Setup Guide** | [docs/SETUP.md](docs/SETUP.md) | Environment setup, WSL2, offline deployment |
| **Offline Linux Guide** | [docs/OFFLINE_LINUX.md](docs/OFFLINE_LINUX.md) | Air-gapped Linux deployment instructions |
| **Graph Engine** | [GRAPH_ENGINE.md](GRAPH_ENGINE.md) | Graph construction, typology detector internals |
| **Deadlock Protocol** | [DEADLOCK_PROTOCOL.md](DEADLOCK_PROTOCOL.md) | Concurrency safety and race-condition handling |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) | Version history and development log |
