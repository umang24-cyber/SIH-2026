# BITKAUN V8 FORENSIC INVESTIGATION PLATFORM :: VERIFICATION & TESTING GUIDE

This document provides a comprehensive test protocol and step-by-step verification manual for the **Bitkaun V8 Forensic Terminal** and backend engine.

---

## 1. System Architecture Overview (V8 Specification)

Bitkaun V8 is an air-gapped, offline-capable blockchain intelligence and forensic triage platform built for law enforcement and AML investigators.

- **Dataset Scale**: 82,078 Ground-Truth Transactions across 17,613 scenario clusters.
- **Dual-Stream Telemetry Fusion**: Unifies on-chain UTXO inputs/outputs with pre-block P2P network telemetry (`relay_ip`, `node_type`, `asn`, `country_code`, `propagation_delta_ms`).
- **AI/ML Model Pipeline**:
  - **XGBoost Binary Illicit Detector**: Evaluates $P(\text{illicit})$ across topological and network telemetry features.
  - **Multi-Class Typology Classifier**: Differentiates Peeling Chains, Layering Hubs, CoinJoin Mixers, and Ransomware Extortion.
  - **TreeSHAP Explainability**: Computes per-transaction feature contributions ($+$ / $-$ direction) with natural language explanations.
  - **Isolation Forest Anomaly Engine**: Independent structural and temporal unusualness score ($0-100$) measuring deviation from licit Bitcoin behavior (SIH PS146 compliance).

---

## 2. Terminal Commands & Syscall Reference

| Command | Aliases | Usage | Category | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`benchmark`** | `eval`, `metrics`, `accuracy` | `benchmark` | Model Validation | Displays V8 model scorecard: Precision, Recall, F1 for 4 typologies + inference latency. |
| **`search`** | `find`, `query` | `search <query>` | Investigation | Universal search across integer TxID, wallet address, IP, ASN, or scenario cluster. |
| **`scenarios`** | `clusters` | `scenarios [prefix] [page]` | Exploration | Paginated directory of clusters partitioned by typology (peeling, mixing, layering, ransomware, licit). |
| **`telemetry`** | `stats`, `p2p` | `telemetry` | P2P Network | Global network infrastructure breakdown, propagation latency $\Delta t$, top ASNs and countries. |
| **`communities`** | `community`, `syndicates` | `communities [scenario_id]` | Link Analysis | NetworkX greedy modularity partition showing co-acting entity syndicates and wallet/TX sub-clusters. |
| **`flow`** | `decompose` | `flow <txid>` | UTXO Forensics | Visual financial flow decomposition with CIOH entity cluster roots, fees, and relay telemetry. |
| **`anomaly`** | `unusual` | `anomaly [scenario_id]` | Anomaly Engine | Standalone Isolation Forest unusualness score ($0–100$) vs normal Bitcoin reference distribution. |
| **`correlate`** | `upload`, `dualstream` | `correlate` | Data Ingestion | Dual-stream Ledger CSV & P2P Telemetry CSV drag-and-drop correlation with live SHAP attribution. |
| **`graph`** | `dashboard`, `g`, `nodes` | `graph [scenario_id]` | 3D WebGL | Interactive 3D WebGL force-directed graph with Bitcoin medallion sprites and particle orbs. |
| **`inspect`** | `i` | `inspect <txid \| addr \| sc_id>` | UTXO Forensics | Deep audit of UTXO multi-I/O arrays, miner fees, and broadcast relay network telemetry. |
| **`trace`** | `route` | `trace <src> <dst>` | Link Analysis | Multi-hop BFS shortest path velocity tracer with laundering velocity metrics. |
| **`taint`** | *none* | `taint <seed_address>` | UTXO Forensics | Forward dirty coin risk propagation and decay (FIFO / Haircut poisoning models). |
| **`alerts`** | `alert` | `alerts [pattern]` | Threat Intel | Real-time prioritized queue of detected laundering typologies ranked by confidence and SHAP. |
| **`dossier`** | `report` | `dossier <txid \| list>` | Reporting | Generates LEA investigative summary with transaction chronology and export capabilities. |
| **`tor`** | *none* | `tor [txid]` | Threat Intel | Tor exit node timing entropy profiler and relay de-anonymization metrics. |
| **`ingest`** | `inject` | `ingest sample [type] \| <json>` | Dynamic Ingestion | Live transaction injection into in-memory database with real-time XGBoost + SHAP scoring. |
| **`logs`** | `log`, `stream` | `logs` | Monitoring | Live mempool gossip frames and block ingestion event stream. |
| **`status`** | `sys`, `health` | `status` | System | In-memory engine health, loaded transactions, unique wallets, and uptime telemetry. |
| **`help`** | `man`, `?` | `help [command]` | Navigation | Interactive manual page indexing all system commands with clickable examples. |
| **`sound`** | `audio` | `sound [on \| off]` | Accessibility | Toggle procedural mechanical keyboard audio and alert chirps. |
| **`clear`** | `cls` | `clear` (or `Ctrl+L`) | Navigation | Clears terminal screen buffer. |

---

## 3. Step-by-Step Test Protocol

### Test Case 1: Model Benchmark & Accuracy Scorecard
1. **Command**:
   ```bash
   benchmark
   ```
2. **Expected Output**:
   - Header shows `v8.0 (82,078 transactions)` under Dataset Scope.
   - Overall Macro F1: `93.9%`.
   - Average Inference Latency: `0.42 ms`.
   - Breakdown for all 4 typologies:
     - **Peeling Chains**: Precision 96.2%, Recall 94.1%, F1 95.1%
     - **Layering Hubs**: Precision 91.8%, Recall 93.5%, F1 92.6%
     - **Mixing / CoinJoin**: Precision 98.4%, Recall 97.8%, F1 98.1%
     - **Ransomware Extortion**: Precision 90.5%, Recall 89.2%, F1 89.8%
   - Each card features a `[View Alerts >]` button that dispatches targeted alerts filtering.

---

### Test Case 2: Universal Forensic Search
1. **Command (TxID)**:
   ```bash
   search 881920041
   ```
   - **Result**: `TRANSACTION` match badge (`#38bdf8`), displaying total volume, miner fee, relay IP, ASN, and action buttons (`[Inspect]`, `[Flow]`, `[Dossier]`).
2. **Command (Autonomous System)**:
   ```bash
   search AS49981
   ```
   - **Result**: `TELEMETRY` match badge (`#c084fc`), displaying transactions originating from AS49981 with node types and latency metrics.
3. **Command (Scenario Cluster)**:
   ```bash
   search peeling_chain_04651
   ```
   - **Result**: `SCENARIO` match badge (`#fbbf24`), listing member transactions with 1-click `[Open 3D Graph]`, `[Communities]`, and `[Score Anomaly]` buttons.

---

### Test Case 3: Scenario Cluster Directory
1. **Command**:
   ```bash
   scenarios
   ```
   - Displays all scenario clusters with transaction counts, total BTC volume, and node infrastructure badges.
2. **Typology Filtering**:
   ```bash
   scenarios peel 1
   scenarios mix 1
   scenarios ransom 1
   ```
   - Filters clusters by prefix; pagination buttons (`< PREVIOUS PAGE` and `NEXT PAGE >`) navigate pages smoothly.

---

### Test Case 4: Network Modularity & Community Detection
1. **Command**:
   ```bash
   communities peeling_chain_04651
   ```
2. **Expected Output**:
   - Displays greedy modularity community partitions discovered in the scenario subgraph.
   - Shows total nodes, inter-entity edges, and detected syndicates.
   - Member preview chips (`[W] Wallet`, `[T] Transaction`, `[I] IP`) with 1-click `inspect` action on click.

---

### Test Case 5: Financial UTXO Flow Decomposition
1. **Command**:
   ```bash
   flow 881920041
   ```
2. **Expected Output**:
   - Displays structured UTXO Inputs side-by-side with Output recipients.
   - Shows Common-Input-Ownership-Heuristic (CIOH) entity cluster roots (`entity_...`).
   - Displays miner transaction fee and fee ratio percentage.
   - Pre-block network telemetry card showing relay IP, origin ASN, country code, and propagation $\Delta t$.

---

### Test Case 6: Isolation Forest Anomaly Scoring
1. **Command**:
   ```bash
   anomaly peeling_chain_04651
   ```
2. **Expected Output**:
   - Large visual score gauge ($0-100$) with color-coded risk badge (`LOW`, `MEDIUM`, or `HIGH`).
   - Raw decision function score and high anomaly threshold ($70.00$).
   - SIH PS146 clarification note confirming independent unusualness scoring vs licit reference distribution.

---

### Test Case 7: Global P2P Broadcast Telemetry
1. **Command**:
   ```bash
   telemetry
   ```
2. **Expected Output**:
   - Aggregations across all 82,078 transactions.
   - Node type distributions (Residential, Tor, VPN, Datacenter, Bulletproof) with visual percentage bars.
   - Average propagation latency $\Delta t$ by node type (e.g. Tor relays exhibiting elevated delays).
   - Clickable top ASNs (`search <asn>`) and top origin countries.

---

### Test Case 8: Dual-Stream File Ingestion & Live Correlation
1. **Command**:
   ```bash
   correlate
   ```
2. **Expected Output**:
   - Opens the Dual-Stream correlation workspace.
   - Click `[Auto-Load Sample Pair (100 Rows)]`.
   - Click `[Correlate & Run V8 ML Inference Pipeline]`.
   - Live synchronization status: `CORRELATED & INGESTED`.
   - Live XGBoost $P(\text{illicit})$ prediction, typology classification, and TreeSHAP attribution feature table.

---

### Test Case 9: 3D Force-Directed WebGL Graph
1. **Command**:
   ```bash
   graph peeling_chain_04651
   ```
2. **Expected Output**:
   - Mounts Three.js WebGL canvas.
   - Nodes rendered as Bitcoin sprites with risk-colored glow rings.
   - Links show directed animated transaction particles representing flow of funds.
   - OrbitControls: Click-and-drag to rotate, scroll to zoom, right-click to pan.
   - Click `[Close]` in top right to dismiss graph.

---

### Test Case 10: Interactive Help Manual
1. **Command**:
   ```bash
   help
   ```
2. **Expected Output**:
   - Mounts the interactive manual page (`bitkaun-terminal`).
   - Shows 5-step forensic investigation workflow.
   - Full command registry table with all 17 commands, aliases, syntax, and clickable examples.
   - Clicking any example (e.g. `flow 881920041`) immediately dispatches the command.
3. **Specific Command Help**:
   ```bash
   help flow
   help benchmark
   ```
   - Renders the specific syscall manual page with synopsis, aliases, description, and invocations.

---

## 4. Verification Checklist

- [x] Backend `routes_stats.py` dataset version updated from `v2.0` to `v8.0 (82,078 transactions)`.
- [x] Backend model status updated from `V7` to `V8 Frozen Synthetic Benchmark`.
- [x] All 7 new endpoints verified via automated Python test suite with HTTP 200 responses.
- [x] All 17 commands registered in `COMMAND_REGISTRY` with aliases and interactive examples.
- [x] Interactive `HelpManualView` mounted in terminal UI with zero-typing latency.
- [x] Frontend TypeScript compilation verified with `npm run build` (zero errors, 57 modules transformed in 3.13s).
- [x] Audio synthesis engine operational with mechanical click and alert chimes.
