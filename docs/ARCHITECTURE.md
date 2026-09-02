# System Architecture — Bitcoin AML Forensics Platform

## 1. End-to-End System Pipeline

```text
+-----------------------------------------------------------------------------------------------------------------+
|                                                 RAW DATA LAYER                                                  |
|                                                                                                                 |
|  data/processed/blockchain_transactions.csv                                data/processed/network_metadata.csv  |
|  Columns:                                                                 Columns:                              |
|  - txid, timestamp, script_type, fee_btc                                 - txid, relay_timestamp, relay_ip     |
|  - input_addresses, output_addresses (JSON Arrays)                        - relay_port, node_type, country_code |
|  - input_amounts, output_amounts (JSON Arrays)                            - asn, isp, protocol_version          |
|  - scenario_id, split                                                     - user_agent, scenario_id, split      |
|  - is_illicit, pattern_type (Ground Truth Labels)                                                               |
+-------------------------------------------------------+---------------------------------------------------------+
                                                        |
                                                        | Joined on txid (Primary Key)
                                                        v
+-----------------------------------------------------------------------------------------------------------------+
|                                       INGESTION & JSON PARSING LAYER (P6)                                       |
|  - Load CSVs via Pandas; parse JSON array columns with json.loads()                                             |
|  - Verify 1:1 row alignment and zero nulls per validate_v2.py                                                  |
+------------------------------------+---------------------------------------------------+------------------------+
                                     |                                                   |
                                     | Structural & Graph Data                           | Feature Columns
                                     v                                                   v
+----------------------------------------------------+  +---------------------------------------------------------+
|             GRAPH ENGINE & HEURISTICS (P4)         |  |             FEATURE EXTRACTION & ML ENGINE (P5)         |
|                                                    |  |                                                         |
|  Nodes:                                            |  |  Safe Features Extracted:                               |
|  - Wallet (address, is_licit_exchange)             |  |  - Financial: total_input, total_output, fee_btc,       |
|  - Transaction (txid, timestamp, fee_btc, etc.)    |  |               fee_ratio, num_inputs, num_outputs        |
|  - IP (relay_ip, country, asn, isp, node_type)     |  |  - Script: script_type (One-Hot / Categorical)          |
|  Edges:                                            |  |  - Timing: propagation_delta_ms (timestamp-relay_time) |
|  - SENT (Wallet -> Tx, amount_btc)                 |  |  - Network: node_type, country_code, asn, isp           |
|  - RECEIVED (Tx -> Wallet, amount_btc)             |  |  - Graph Centrality: in_degree, out_degree, pagerank    |
|  - BROADCAST (IP -> Tx, relay_timestamp, etc.)     |  |                                                         |
|  Typology Detectors:                               |  |  Group CV Strategy: scenario_id GroupKFold              |
|  - peeling_chain (1->2 out, change-reuse chains)   |  |  Model: XGBoost / LightGBM Multi-class Classifier       |
|  - layering (fan-out N then fan-in N)              |  |  Explainability: TreeSHAP Feature Attribution           |
|  - mixing (N->N equal-value multi-round CoinJoin)  |  |                                                         |
+------------------------------------+---------------+  +----------------------------+----------------------------+
                                     |                                               |
                                     | Flagged Candidate Subgraphs                   | Risk Score & SHAP Values
                                     +-----------------------+-----------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------------------------------------------------+
|                                         ALERT & RANKING ENGINE (P5, P6)                                         |
|  - Correlate graph typology candidate subgraphs with ML classification confidence                               |
|  - Rank alerts: Severity = f(ML Confidence, Typology Match, High-Risk Infrastructure)                           |
|  - Synthesize human-readable forensic justification strings                                                    |
+------------------------------------------------------------+----------------------------------------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------------------------------------------------+
|                                            FASTAPI REST BACKEND (P6)                                            |
|  - GET /entity/{address}          GET /transaction/{txid}          GET /graph/{scenario_id}                     |
|  - GET /alerts                    GET /alerts/{candidate_id}/evidence                                           |
+------------------------------------------------------------+----------------------------------------------------+
                                                             |
                                                             v
+-----------------------------------------------------------------------------------------------------------------+
|                                    INVESTIGATION DASHBOARD (P1, P2)                                             |
|  - Interactive Link Analysis Network (Cytoscape.js / vis.js)                                                    |
|  - Ranked Alert Inbox, Filtering, Risk Heatmaps, and Exportable Forensic Evidence Dossiers                      |
+-----------------------------------------------------------------------------------------------------------------+
```

---

## 2. Critical System Invariant: Zero Label Leakage

> ### ⚠️ SYSTEM-LEVEL ARCHITECTURAL INVARIANT
> The ground-truth columns **`is_illicit`** and **`pattern_type`** MUST NEVER be ingested, referenced, or used as input features by:
> 1. Graph construction algorithms
> 2. Typology detection heuristics (`peeling_chain`, `layering`, `mixing`)
> 3. Machine learning feature extraction pipelines or inference models
> 4. Alert ranking heuristics
>
> **Permitted Usage:** `is_illicit` and `pattern_type` flow **ONLY** into offline validation scripts and evaluation pipelines (e.g., computing precision, recall, ROC-AUC, confusion matrices) and for generating synthetic benchmark evaluation reports.
>
> Automated unit test assertions must enforce this exclusion in `tests/test_ml_safety.py`.

---

## 3. Data Flow by Column

| Column Name | Ingestion (P6) | Graph Construction (P4) | ML Feature Extractor (P5) | ML / Model Eval (P5) | API Response (P6) |
|---|---|---|---|---|---|
| `txid` | Primary Key | Transaction Node ID | Entity Index / Join Key | Eval Join Key | Serialized in API |
| `timestamp` | UTC Datetime | Transaction Node Property | `propagation_delta_ms` | — | Serialized in API |
| `input_addresses` | JSON parse | Wallet Nodes & `SENT` Edges | Feature `num_inputs` | — | Serialized in API |
| `output_addresses` | JSON parse | Wallet Nodes & `RECEIVED` Edges | Feature `num_outputs` | — | Serialized in API |
| `input_amounts` | JSON parse | `SENT` Edge `amount_btc` | `total_input`, stats | — | Serialized in API |
| `output_amounts` | JSON parse | `RECEIVED` Edge `amount_btc` | `total_output`, stats | — | Serialized in API |
| `fee_btc` | Float64 | Transaction Node Property | `fee_ratio = fee / input` | — | Serialized in API |
| `script_type` | Categorical | Transaction Node Property | Categorical Feature | — | Serialized in API |
| `is_illicit` | Ground Truth | 🚫 **EXCLUDED** | 🚫 **EXCLUDED** | Evaluation Target | Admin / Debug only |
| `pattern_type` | Ground Truth | 🚫 **EXCLUDED** | 🚫 **EXCLUDED** | Multiclass Target | Admin / Debug only |
| `scenario_id` | Scenario Key | Graph Cluster Scope | 🚫 Not Feature (Group CV Key) | Group Stratification | Serialized in API |
| `split` | Split Key | — | 🚫 Not Feature (Split Tag) | Train/Test Split Selector | — |
| `relay_timestamp` | UTC Datetime | `BROADCAST` Edge Property | `propagation_delta_ms` | — | Serialized in API |
| `relay_ip` | IP String | IP Node ID | — | — | Serialized in API |
| `relay_port` | Int64 | IP / Edge Property | Feature | — | Serialized in API |
| `node_type` | Categorical | IP Node Property | Categorical Feature | — | Serialized in API |
| `country_code` | ISO Alpha-2 | IP Node Property | Categorical Feature | — | Serialized in API |
| `asn` | AS String | IP Node Property | Categorical Feature | — | Serialized in API |
| `isp` | Org String | IP Node Property | Categorical Feature | — | Serialized in API |
| `protocol_version` | Constant | — | — | — | Serialized in API |
| `user_agent` | Banner String | `BROADCAST` Edge Property | Token / Flag | — | Serialized in API |

---

## 4. Module Boundary Table

| Module Name | Owner | Primary Inputs | Primary Outputs | Consumer Module |
|---|---|---|---|---|
| **Data Ingestion** | P3, P6 | `blockchain_transactions.csv`, `network_metadata.csv` | Parsed DataFrame / In-Memory SQLite | Graph Engine (P4), ML Engine (P5), Backend API (P6) |
| **Graph Construction** | P4 | Parsed transactions, multi-I/O addresses, IP relays | Heterogeneous NetworkX / Subgraph objects | Typology Detectors (P4), API Graph Endpoint (P6) |
| **Typology Detection** | P4 | Graph topologies, transaction flows | Flagged Candidate Subgraphs (`candidate_id`, member txids/wallets, typology heuristic) | ML Classifier (P5), Alert Engine (P6) |
| **Feature Extraction** | P5 | Transaction records, network telemetry, graph degree metrics | Normalized Feature Matrix $X$ (Strictly excluding labels) | ML Training & Inference (P5) |
| **ML Classification & SHAP** | P5 | Feature Matrix $X$, Trained XGBoost/LightGBM model | Predicted class, probabilities, SHAP local attribution vectors | Alert & Ranking Engine (P6) |
| **Backend REST API** | P6 | Graph structures, candidate alerts, SHAP explanations, SQLite data | REST JSON Endpoints conforming to `API_CONTRACT.md` | Investigation Dashboard (P1/P2) |
| **Investigation Dashboard** | P1, P2 | API REST responses (`/alerts`, `/graph/{scenario_id}`, `/alerts/{id}/evidence`) | Interactive UI, Cytoscape.js network graph, forensic alert triage | End-user forensic investigator |
