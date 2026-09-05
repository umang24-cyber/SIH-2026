# Bitcoin AML Graph Engine - Complete Work & Architecture Documentation

## 1. Executive Summary

The **Bitcoin AML Graph Engine** is a high-performance graph analytics and money-laundering typology detection pipeline built for analyzing blockchain transactions cross-referenced with peer-to-peer network layer telemetry.

The engine transforms raw transactional and network metadata into a heterogeneous directed multigraph, executes deterministic and heuristic detection algorithms for complex laundering typologies (Peeling Chains, Fan-out/Fan-in Layering, and CoinJoin Mixing Clusters), enriches structures with infrastructure intelligence (Tor/VPN/Datacenter attribution), exports visualizer-ready graph data and ML feature vectors, and validates results against ground-truth labels.

---

## 2. End-to-End Pipeline Architecture

The pipeline is organized into a modular 6-step workflow orchestrated by [`main.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/main.py):

```
+---------------------------------------------------------------------------------------+
|                                    1. INGEST                                          |
|  - Load blockchain_transactions.csv & network_metadata.csv                            |
|  - Parse JSON-encoded arrays (addresses, amounts)                                     |
|  - Validate schema, data types, timestamp alignment, and join integrity on `txid`    |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                  2. GRAPH BUILD                                       |
|  - Construct Full Heterogeneous DiGraph G (wallet, transaction, ip nodes)            |
|  - Construct Wallet-to-Wallet MultiDiGraph Projection P (preserves amount & timing)   |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                              3. TYPOLOGY DETECTION                                    |
|  - Peeling Chain Detector (Greedy UTXO carry-forward tracking & amount decay)         |
|  - Layering Detector (Fan-out discovery & multi-hop reconvergence BFS search)         |
|  - Mixing Detector (Co-participation bipartite projection + Louvain community clustering)|
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                              4. FEATURE ENRICHMENT                                    |
|  - Cross-reference candidate nodes with broadcast network layer telemetry             |
|  - Compute: unique_ips, unique_asns, tor_vpn_fraction, amount decay, CV, time spans   |
|  - Flatten candidate vectors for machine learning handoff                             |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                   5. EXPORT                                           |
|  - `graph_export.json`: Full annotated subgraphs + candidate tags for UI visualizer   |
|  - `candidates_ml_handoff.csv`: Flat feature-vector matrix for downstream classifiers |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            v
+---------------------------------------------------------------------------------------+
|                                 6. VALIDATION                                         |
|  - Ground-truth validation against scenario labels (without leaking labels to logic)  |
|  - Evaluate Precision, Recall, F1 score, and False-Positive distributions             |
|  - `validation_report.json`: Comprehensive audit and scenario coverage report         |
+---------------------------------------------------------------------------------------+
```

---

## 3. Module Breakdown & Implemented Work

### 3.1. Ingestion Engine ([`graph_engine/ingest.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/ingest.py))
* **`RawTxRecord` Schema-Binding Adapter:** Abstracted ingestion layer that decouples the engine from the raw dataset schema. Maps variable CSV field names into a consistent internal `RawTxRecord` dataclass, preventing downstream breakage if the incoming data schema changes.
* **CSV Parsing & Unpacking:** Reads `blockchain_transactions.csv` and `network_metadata.csv`, decoding stringified array representations for `input_addresses`, `input_amounts`, `output_addresses`, and `output_amounts`.
* **Join Verification:** Executes a strict inner join on `txid`, verifying row parity with zero transaction drops.
* **Integrity Validation:** Enforces positive amounts, valid timestamps, non-empty addresses, and valid fee conservation. Rows failing hard validation (e.g., missing timestamps or empty inputs/outputs) are flagged and skipped.

### 3.2. Graph Construction ([`graph_engine/graph_build.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/graph_build.py))
* **Full Heterogeneous Directed Graph ($G$):**
  * **Type:** `networkx.MultiDiGraph` (defensive correctness against duplicate network relay events and parallel intra-transaction paths).
  * **Nodes:**
    * `wallet` (`w:<address>`): Bitcoin addresses with in/out degree metrics.
    * `transaction` (`tx:<txid>`): Individual Bitcoin transactions with fee, script type, and timestamp.
    * `ip` (`ip:<relay_ip>`): Network broadcast relay nodes with ASN, ISP, country code, and infrastructure classification.
  * **Edges:**
    * `SENT`: `wallet` $\to$ `transaction` (contains `amount_btc`).
    * `RECEIVED`: `transaction` $\to$ `wallet` (contains `amount_btc`).
    * `BROADCAST`: `ip` $\to$ `transaction` (contains relay timestamp, port, and user agent).
  * **Structural Validation:** Includes `verify_bipartite(G)` to assert graph integrity (no direct wallet $\to$ wallet or transaction $\to$ transaction edges, and proper degree distribution constraints).
* **Wallet-to-Wallet Projection ($P$):**
  * `MultiDiGraph` projecting direct transfers from sender wallets to recipient wallets across transactions: $w_A \xrightarrow{\text{SENT}} tx_T \xrightarrow{\text{RECEIVED}} w_B \implies w_A \xrightarrow{(txid, amount, timestamp, fee, script\_type)} w_B$.
  * Explicitly preserves multi-edge granularity and time ordering without collapsing or netting amounts.

### 3.3. Shared Structures ([`graph_engine/structures.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/structures.py))
* **`CandidateStructure` Dataclass:**
  * `candidate_id`: Unique identifier (e.g., `peel_0001`, `layer_0003`, `mix_0012`).
  * `candidate_type`: Typology classification string (`peeling_chain`, `layering`, `mixing`).
  * `member_txids`: List of member transaction IDs.
  * `member_wallets`: List of member wallet addresses.
  * `member_ips`: List of relay IP addresses resolved during feature enrichment.
  * `features`: Typology-specific and network feature dictionary.
  * `hop_sequence`: Ordered step-by-step transfer log for linear/fan structures.

---

## 4. Typology Detection Algorithms

### 4.1. Peeling Chain Detector ([`graph_engine/detectors/peeling_chain.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/detectors/peeling_chain.py))
* **Concept:** A money laundering pattern where a large UTXO is repeatedly split into a smaller peeled payment (payment/cash-out) and a larger carry-forward change address across consecutive transactions.
* **Algorithm:**
  1. **Seed Identification:** Identify all 1-to-2 or 2-to-2 transactions with a clear asymmetric amount split.
  2. **Greedy Forward Extension:** Trace the carry-forward wallet address into its subsequent spending transaction.
  3. **Temporal & Value Consistency:** Ensure transaction time gap $\le 6\text{ hours}$ (`PEEL_MAX_HOP_GAP_SECONDS`), carry amount strictly decays with tolerance $\le 5\%$ (`PEEL_AMOUNT_TOLERANCE`), and downstream transactions continue the 2-output structure.
  4. **Filtering & Deduplication:** Filter chains shorter than $\ge 3\text{ hops}$ (`PEEL_MIN_CHAIN_LENGTH`) and remove strict sub-chains.

### 4.2. Layering Detector ([`graph_engine/detectors/layering.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/detectors/layering.py))
* **Concept:** Rapid dispersal of funds from a single source across multiple intermediate intermediary wallets (fan-out), followed by reconvergence into a consolidation sink wallet (fan-in).
* **Algorithm:**
  1. **Fan-Out Identification:** Identify source wallets with unique out-degree $\ge 5$ (`LAYER_MIN_FANOUT_DEGREE`) in the wallet projection $P$.
  2. **Bounded BFS Forward Exploration:** For every recipient $R_i$, execute forward Breadth-First Search up to 3 hops (`LAYER_MAX_RECONVERGENCE_HOPS`).
  3. **Reconvergence Ratio:** Calculate the fraction of recipients reaching candidate sink wallet $C$. Accept if ratio $\ge 60\%$ (`LAYER_MIN_RECONVERGENCE_RATIO`).
  4. **Exchange Hub Suppression:** Query total node degree in $G$ to filter known high-degree exchange hubs ($> 500\text{ transactions}$).
  5. **Temporal Windowing:** Ensure total duration between initial fan-out and final fan-in is $\le 72\text{ hours}$ (`LAYER_MAX_TIME_WINDOW_SECONDS`).

### 4.3. Mixing Detector ([`graph_engine/detectors/mixing.py`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/graph_engine/detectors/mixing.py))
* **Concept:** CoinJoin-style mixing protocols where multiple independent parties co-sign transactions with identical or standardized output denominations to break transaction graph heuristics.
* **Algorithm:**
  1. **Bipartite Co-Participation Graph ($CP$):** For all transactions with $\ge 3\text{ inputs}$ and $\ge 3\text{ outputs}$, add co-participation edges between all co-signing input wallets.
  2. **Community Detection:** Apply Louvain modularity optimization (`community_louvain.best_partition`) on $CP$ with reproducible random seed (`config.LOUVAIN_RANDOM_STATE = 42`).
  3. **Structural Filters:**
     * Community size $n \ge 5$ wallets (`MIX_MIN_COMMUNITY_SIZE`).
     * Internal subgraph density $\ge 0.30$ (`MIX_MIN_DENSITY`).
     * External connectivity ratio $\le 0.40$ (`MIX_MAX_EXTERNAL_RATIO`).
     * Output amount Coefficient of Variation $CV = \frac{\sigma}{\mu} \le 0.50$ (`MIX_MAX_AMOUNT_CV`).
     * Maximum time span $\le 48\text{ hours}$ (`MIX_MAX_TIME_WINDOW_SECONDS`).

---

## 5. Performance Optimizations Implemented

During development, major algorithmic bottlenecks were resolved to allow instantaneous graph processing:

1. **Layering Incident Edge Optimization:**
   * *Problem:* Previous implementation iterated over the entire graph's edge set ($291,266\text{ edges}$) inside the fan-out loop ($12,875\text{ sources}$), resulting in $> 3.75\text{ billion}$ loop iterations that locked execution.
   * *Solution:* Replaced full edge scans with direct node-incident lookups `P.out_edges(source, data=True)` and `P.in_edges(sink, data=True)`, reducing execution time from minutes/hang to **$2.0\text{ seconds}$**.
2. **Induced Subgraph Community Calculations in Mixing:**
   * *Problem:* Density and boundary calculations scanned global edge lists repeatedly.
   * *Solution:* Leveraged NetworkX induced subgraphs `CP.subgraph(wallet_set)` and degree-sum boundary equations, running in **$< 1\text{ second}$**.
3. **$O(1)$ Edge Candidate Membership Mapping in Export:**
   * *Problem:* Edge serialization iterated over all candidates for each of the $409,578\text{ edges}$ ($O(|E| \times |candidates|)$).
   * *Solution:* Created precomputed node-to-candidate index maps, resolving candidate tagging in $O(1)$ per edge.
4. **Console Encoding Safety:**
   * Handled Windows `cp1252` encoding constraints to prevent stream truncation.

---

## 6. Pipeline Benchmark & Results

Execution benchmark on the full dataset (**82,078 transactions**, **448,556 nodes**, **409,578 edges**):

| Step | Operation | Execution Time | Output Summary |
| :--- | :--- | :---: | :--- |
| **Step 1** | **Ingest** | `3.3s` | 82,078 rows loaded and validated |
| **Step 2** | **Graph Build** | `8.6s` | 448,556 nodes, 409,578 edges built |
| **Step 3** | **Typology Detection** | `5.3s` | 158 total candidate structures detected |
| **Step 4** | **Feature Enrichment** | `0.5s` | Network features & infrastructure metadata appended |
| **Step 5** | **Export** | `15.8s` | 196.4 MB JSON + ML Feature CSV generated |
| **Step 6** | **Validation** | `0.1s` | Ground truth evaluation completed |
| **Total** | **End-to-End Pipeline** | **33.6s** | **All steps completed successfully** |

---

## 7. Ground-Truth Validation Metrics

Evaluation against labelled synthetic ground truth:

| Typology | Detected Candidates | True Positives (TP) | False Positives (FP) | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`peeling_chain`** | **40** | 40 | 0 | **1.0000** | **0.8163** | **0.8989** |
| **`layering`** | **42** | 25 | 17 | **0.5952** | **1.0000** | **0.7463** |
| **`mixing`** | **76** | 13 | 63 | **0.1711** | **0.1477** | **0.1585** |
| **Overall** | **158** | **78** | **80** | **0.4937** | — | — |

---

## 8. Exported Artifacts

The pipeline generates three deliverables in [`output/`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/output):

1. **[`graph_export.json`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/output/graph_export.json) (196.4 MB):**
   * Complete heterogeneous node & edge topology.
   * Annotated candidate memberships for frontend 3D/2D visualization (`candidate_ids` join keys).
   * Formatted ISO-8601 timestamps and numeric BTC amounts.
2. **[`candidates_ml_handoff.csv`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/output/candidates_ml_handoff.csv):**
   * 158 candidate rows $\times$ 25 feature columns.
   * Includes structural metrics (`chain_length`, `total_peeled_btc`, `fan_out_degree`, `cluster_density`, `output_amount_cv`) and network layer metrics (`unique_ips`, `unique_asns`, `tor_vpn_fraction`).
3. **[`validation_report.json`](file:///c:/Users/HP/OneDrive/Desktop/SIH-2026/output/validation_report.json):**
   * Detailed per-candidate TP/FP breakdown, dominant pattern analysis, and scenario coverage reports.

---

## 9. How to Execute

### Standard Pipeline Run
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main
```

### Custom Data & Output Paths
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main --data-dir "data/processed" --output-dir "output"
```

### Fast Run (Skip Ground-Truth Validation)
```powershell
.\graph_engine\.venv\Scripts\python -m graph_engine.main --no-validate
```
