# Graph Construction & Typology Detection Specification

> **Owner:** P4 (Graph Engineering)  
> **Source of Truth Reference:** [DATA_DICTIONARY.md](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md) (Sections 7a, 7b, 7c) · [API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)

---

## 1. Zero Label Leakage Invariant

> ### ⚠️ HARD SYSTEM CONSTRAINT
> Ground-truth labels **`is_illicit`** and **`pattern_type`** MUST NEVER be used as features or conditions during graph construction or typology detection algorithms. Graph heuristics must operate purely on topological structure, transaction amounts, timestamps, and address connectivity.

---

## 2. Graph Schema Definition

The graph is constructed as a heterogeneous multi-directed graph (using NetworkX for analytics and serializing to JSON for frontend rendering).

### 2a. Node Schema (Exact from `DATA_DICTIONARY.md` Section 7a)

| Node Type | Primary Key | Properties | Description |
|---|---|---|---|
| **`Wallet`** | `address` (string) | `is_licit_exchange` (boolean) | Base58 Bitcoin address. `is_licit_exchange` indicates high-volume exchange node (flagged via degree/clustering heuristics). |
| **`Transaction`** | `txid` (int64) | `timestamp` (string/datetime), `fee_btc` (float64), `script_type` (string), `scenario_id` (string) | Multi-I/O UTXO transaction node. |
| **`IP`** | `relay_ip` (string) | `country_code` (string), `asn` (string), `isp` (string), `node_type` (string), `relay_port` (int64) | P2P origin relay node. |

### 2b. Edge Schema (Exact from `DATA_DICTIONARY.md` Section 7b)

| Edge Type | Direction | Properties | Description |
|---|---|---|---|
| **`SENT`** | `Wallet → Transaction` | `amount_btc` (float64) | Input UTXO consumed by the transaction. Value taken from corresponding index in `input_amounts`. |
| **`RECEIVED`** | `Transaction → Wallet` | `amount_btc` (float64) | Output UTXO created by the transaction. Value taken from corresponding index in `output_amounts`. |
| **`BROADCAST`** | `IP → Transaction` | `relay_timestamp` (string/datetime), `relay_port` (int64), `user_agent` (string) | P2P origin peer broadcast telemetry. |

---

## 3. Typology Detection Heuristics

Per `DATA_DICTIONARY.md` Section 7c, candidate illicit structures are detected using structural graph algorithms:

### 3.1 Peeling Chain Detection (`peeling_chain`)
- **Topological Pattern:** A linear sequence of 1-input $\rightarrow$ 2-output transactions.
- **Structural Heuristic:**
  1. Transaction has 1 input address and 2 output addresses:
     - Output $A$: Smaller amount (peeled payment / illicit destination).
     - Output $B$: Larger amount (change address).
  2. Change address $B$ is subsequently reused as the single input for the next hop transaction within a narrow time window $\Delta t$.
  3. Traversal algorithm traces sequential change-address hops (chain length $\ge 3$) to flag the candidate subgraph.

### 3.2 Layering Detection (`layering`)
- **Topological Pattern:** Rapid dispersion followed by consolidation (Fan-Out $\rightarrow$ Fan-In).
- **Structural Heuristic:**
  1. **Fan-Out:** 1 source address or UTXO splits funds into $N$ distinct intermediate addresses ($N \ge 3$) across 1 or 2 hops.
  2. **Intermediary Stage:** Intermediate addresses perform little to no other activity.
  3. **Fan-In / Reconvergence:** The $N$ intermediate addresses send their balances into 1 common consolidation address within a specified time horizon.

### 3.3 Mixing / CoinJoin Detection (`mixing`)
- **Topological Pattern:** Multi-party equal-denomination anonymization rounds.
- **Structural Heuristic:**
  1. Multi-input, multi-output transactions where $N \text{ inputs} \ge 3$ and $N \text{ outputs} \ge 3$.
  2. Output amounts contain identical or near-identical values (standard denomination mixing, e.g., $0.1$ BTC, $0.5$ BTC, $1.0$ BTC).
  3. Multi-round clustering / community detection (using Louvain or Leiden modularity optimization) to group interconnected mixing participants.

---

## 4. Frontend Graph Export Schema

The output of the graph constructor is exported to the backend API as a JSON structure adhering to `API_CONTRACT.md` endpoint `GET /graph/{scenario_id}`.

- **Agreement:** Early alignment with P1/P2 ensures graph nodes contain `id`, `type`, and `properties`, while edges contain `id`, `source`, `target`, `type`, and `properties`.

---

## 5. Open Decisions & Graph Engineering Tasks

- `[ ]` **[TODO: P4]** Implement NetworkX graph builder reading parsed DataFrames from P6.
- `[ ]` **[TODO: P4]** Implement traversal heuristics for peeling chains, layering reconvergence, and CoinJoin mixing.
- `[ ]` **[TODO: P4]** Lock graph serialization format with P1/P2 for Cytoscape.js rendering.
- `[ ]` **[TODO: P4]** Add unit tests for typology detectors against synthetic candidate scenarios.
