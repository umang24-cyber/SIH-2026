# DATA_DICTIONARY.md — SIH PS 146 Bitcoin AML Dataset

> **Audience:** P4 (Graph Engineer) and P5 (ML Engineer).
> **Last updated:** 2026-09-04 · Data version **v4.0**.

---

## 1. File Inventory

| File | Path | Format | Rows | Size | One-line description |
|------|------|--------|------|------|----------------------|
| `blockchain_transactions.csv` | `data/processed/blockchain_transactions.csv` | CSV (UTF-8, comma-delimited) | 83,812 | ~19 MB | Master on-chain ledger: UTXO array inputs/outputs, BTC amounts, miner fees, script types, ground-truth labels, typology patterns, scenario IDs, and train/test split tags. |
| `network_metadata.csv` | `data/processed/network_metadata.csv` | CSV (UTF-8, comma-delimited) | 83,812 | ~11 MB | Master P2P broadcast telemetry: relay timestamps, relay IPs, ports, decorrelated node types, ASNs, ISPs, user agents, scenario IDs, and split tags. |
| `train_blockchain.csv` | `data/processed/train_blockchain.csv` | CSV | 68,334 | ~15 MB | Pre-split train set (81.5%) of `blockchain_transactions.csv`. |
| `train_network.csv` | `data/processed/train_network.csv` | CSV | 68,334 | ~9 MB | Pre-split train set (81.5%) of `network_metadata.csv`. |
| `test_blockchain.csv` | `data/processed/test_blockchain.csv` | CSV | 15,478 | ~4 MB | Pre-split test set (18.5%) of `blockchain_transactions.csv`. |
| `test_network.csv` | `data/processed/test_network.csv` | CSV | 15,478 | ~2 MB | Pre-split test set (18.5%) of `network_metadata.csv`. |

Both master files (and their corresponding split files) are **row-aligned on `txid`** — row _N_ in one file corresponds to the same transaction as row _N_ in the other after a join (always join on `txid`).

---

## 2. Field-by-Field Dictionary

### 2a. `blockchain_transactions.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Unitless 64-bit integer ID | No | `58234917` | Unique transaction identifier. Generated via hash salt shuffling to eliminate ID sequence leakage. |
| 2 | `timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS` (UTC) | No | `2014-03-15 09:22:41` | Block-confirmation timestamp. Range: 2012–2018 (fully overlapping across licit and illicit classes). |
| 3 | `input_addresses` | `object` (JSON array string) | Array of Base58 strings | No | `["12dhqUGwz..."]` | Array of 1–10 input Bitcoin addresses (UTXO senders). |
| 4 | `output_addresses` | `object` (JSON array string) | Array of Base58 strings | No | `["1EcgU6KKS...", "1PZDhrao8..."]` | Array of 1–14 output Bitcoin addresses (UTXO recipients). Includes wallet reuse for multi-hop graph connectivity. |
| 5 | `input_amounts` | `object` (JSON array string) | Array of floats (BTC) | No | `[0.26361416]` | Array of input BTC amounts corresponding 1:1 with `input_addresses`. |
| 6 | `output_amounts` | `object` (JSON array string) | Array of floats (BTC) | No | `[0.0526, 0.21066308]` | Array of output BTC amounts corresponding 1:1 with `output_addresses`. |
| 7 | `fee_btc` | `float64` | BTC, 8 decimal places | No | `0.00035108` | Miner fee. Satisfies exact accounting identity: `sum(input_amounts) = sum(output_amounts) + fee_btc`. |
| 8 | `script_type` | `object` (string) | Categorical enum | No | `P2PKH` | Bitcoin output script type: `P2PKH` (45%), `P2SH` (25%), `P2WPKH` (25%), `P2WSH` (5%). |
| 9 | `is_illicit` | `int64` | Binary: `0` = licit, `1` = illicit | No | `0` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Target variable. |
| 10 | `pattern_type` | `object` (string) | Categorical enum | No | `peeling_chain` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Values: `normal`, `ransomware`, `peeling_chain`, `layering`, `mixing`. |
| 11 | `scenario_id` | `object` (string) | Identifier string | No | `peel_0001` | Grouping key for leak-free train/test splitting. |
| 12 | `split` | `object` (string) | Categorical: `train` or `test` | No | `train` | Deterministic scenario-level stratified split tag. |

#### Array-Valued Fields
In v3.0, transactions are real multi-input / multi-output UTXO transactions. Columns `input_addresses`, `output_addresses`, `input_amounts`, and `output_amounts` are serialized JSON arrays. Parse them using `json.loads()`.

---

### 2b. `network_metadata.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Foreign key to `blockchain_transactions.csv` | No | `58234917` | Transaction ID mapping 1:1 to the blockchain ledger file. |
| 2 | `relay_timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS.mmm` (UTC) | No | `2014-03-15 09:22:40.812` | P2P broadcast timestamp. Strictly 50–500 ms prior to block `timestamp`. |
| 3 | `relay_ip` | `object` (string) | IPv4 dotted-quad | No | `38.148.127.142` | Origin peer IPv4 address with realistic intra-scenario persistence. |
| 4 | `relay_port` | `int64` | TCP port number | No | `8333` | Origin port (85% standard port `8333`, 15% dynamic/alt ports). |
| 5 | `node_type` | `object` (string) | Categorical enum | No | `residential` | Infrastructure classification. Overlapping pools: `residential`, `datacenter`, `mobile`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`. |
| 6 | `country_code` | `object` (string) | ISO 3166-1 alpha-2 | No | `US` | Origin country code (100% overlap between licit and illicit across 16 countries). |
| 7 | `asn` | `object` (string) | `AS` prefix + number | No | `AS7922` | Autonomous System Number. 25 distinct global ASNs. |
| 8 | `isp` | `object` (string) | Org name string | No | `Comcast Cable` | ISP / network infrastructure provider name. |
| 9 | `protocol_version` | `int64` | Bitcoin protocol version | No | `70015` | Constant `70015`. |
| 10 | `user_agent` | `object` (string) | Bitcoin client banner | No | `/Satoshi:22.0.0/` | Node software identifier string. |
| 11 | `scenario_id` | `object` (string) | Grouping string | No | `peel_0001` | Identical to `scenario_id` in blockchain file. |
| 12 | `split` | `object` (string) | Categorical enum | No | `train` | Identical to `split` in blockchain file. |

---

## 3. Ground Truth / Labels

### Label Columns

| Column | Role | Values | Distribution |
|--------|------|--------|--------------|
| `is_illicit` | **Binary class label** | `0` (licit), `1` (illicit) | 48,421 licit (57.8%) / 35,391 illicit (42.2%) |
| `pattern_type` | **Multi-class typology label** | `normal`, `ransomware`, `peeling_chain`, `layering`, `mixing` | • `normal`: 48,421<br>• `ransomware`: 28,000<br>• `peeling_chain`: 2,915<br>• `mixing`: 2,418<br>• `layering`: 2,058 |

### ⚠️ Ground-Truth Leakage Warning & Exclusion List

> [!WARNING]
> **P5 ML Engineers must HARD-DROP the following fields before training:**
> ```
> is_illicit
> pattern_type
> is_licit_exchange (if derived in graph features)
> ```
> `is_licit_exchange` is derived in part from the ground-truth licit label and exchange topology. It must NEVER be fed into an ML classifier.
> Furthermore, scenario grouping keys (`scenario_id`) and split indicators (`split`) are evaluation management keys, NOT ML features.

---

## 4. Scenario Identifiers & Train/Test Split

`scenario_id` groups all transactions and wallets belonging to the same laundering campaign, ransomware operation, exchange cluster, or licit user activity session.

### Deterministic Scenario-Level Split Rules
- **Stratified Group Split**: Split performed strictly at scenario level (`test_size=0.2`, `random_state=42`) stratified by `(is_illicit, pattern_type)`.
- **Zero Leakage**: 100% of transactions for any given `scenario_id` reside strictly in `train` or `test`, never both.
- **Stratification Result**:
  - `train`: 68,334 rows (42.2% illicit) across 4,824 scenarios.
  - `test`: 15,478 rows (42.1% illicit) across 1,207 scenarios.
  - **Shared Scenarios**: `train ∩ test = 0`.

---

## 5. Hard Negatives

To prevent models from relying on simple transaction volume or degree count as a trivial illicit separator:
- Injected **40 synthetic high-activity licit exchange clusters** (6,402 total transactions).
- Each exchange processes 60 to 260 transactions with realistic fan-out withdrawals and fan-in deposits.
- All exchange transactions are marked with `is_illicit = 0` and `pattern_type = normal`.
- 36 exchange wallets have >= 50 transactions as input senders.

---

## 6. Join / Integrity Validation Report

All 15 automated integrity checks in `data_pipeline/validate_v2.py` pass 100%:

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Row Count Match | ✅ PASS | Blockchain: 83,812 \| Network: 83,812 |
| 2 | Key Alignment | ✅ PASS | 0 orphan txids in either direction |
| 3 | Duplicate txids | ✅ PASS | 0 duplicates across all 83,812 rows |
| 4 | Timing Logic | ✅ PASS | 0 violations (`relay_timestamp <= timestamp`) |
| 5 | Null Values | ✅ PASS | 0 null values across all columns in both files |
| 6 | Array Column Parsing | ✅ PASS | Valid JSON, length of addresses == length of amounts |
| 7 | Accounting Identity | ✅ PASS | `sum(inputs) = sum(outputs) + fee` (max residual 0.00000000) |
| 8 | Typology Distribution | ✅ PASS | All 5 pattern_types present (`normal`, `ransomware`, `peeling_chain`, `layering`, `mixing`) |
| 9 | Scenario_id Coverage | ✅ PASS | 100% non-null coverage across 6,031 distinct scenario IDs |
| 10 | Hard Negatives | ✅ PASS | 36 licit wallets with >= 50 transactions each |
| 11 | Network Decorrelation | ✅ PASS | Overlapping pools: suspicious types in licit, normal in illicit |
| 12 | Txid Uniformity | ✅ PASS | Hash-shuffled IDs; max illicit concentration in 500-txid window = 48.8% |
| 13 | Timestamp Overlap | ✅ PASS | Both licit and illicit rows span 2012–2016 and 2017–2018 |
| 14 | Split Integrity | ✅ PASS | 0 leaking scenarios between train and test splits |
| 15 | Split Stratification | ✅ PASS | Train illicit %: 42.2%, Test illicit %: 42.1% (diff: 0.1pp) |

---

## 7. Graph Construction Notes (for P4)

### 7a. Node Types

| Node Type | Key | Properties |
|-----------|-----|------------|
| **Wallet** | `address` (string) | `is_licit_exchange` (⚠️ Graph visualization only; NOT an ML feature) |
| **Transaction** | `txid` (int64) | `timestamp`, `fee_btc`, `script_type`, `scenario_id` |
| **IP** | `relay_ip` (string) | `country_code`, `asn`, `isp`, `node_type`, `relay_port` |

### 7b. Edge Types

| Edge | Direction | Properties |
|------|-----------|------------|
| **SENT** | `Wallet → Transaction` | `amount_btc` (from corresponding index in `input_amounts`) |
| **RECEIVED** | `Transaction → Wallet` | `amount_btc` (from corresponding index in `output_amounts`) |
| **BROADCAST** | `IP → Transaction` | `relay_timestamp`, `relay_port`, `user_agent` |

### 7c. Multi-Input / Multi-Output Graph Structure
Each `txid` represents a multi-input / multi-output UTXO node:
- **Peeling chains**: Variable 4–28 hops, including multi-input consolidation peels, multi-output peels, and branching tree peels.
- **Layering**: Multi-tier fan-out (3–12 outputs), intermediary sub-splits and pass-throughs, and multi-collector fan-ins.
- **Mixing**: Pre-mix split transactions (Tx0), multi-round equal/unequal CoinJoin mixing (2–8 rounds, 3–8 participants), and post-mix consolidation transfers.

---

## 8. ML-Ready Notes (for P5)

### 8a. Feature Safety Matrix

| Category | Columns | Safe as Direct Features? | Notes |
|----------|---------|--------------------------|-------|
| **Transaction amounts** | `input_amounts`, `output_amounts`, `fee_btc` | ✅ Yes | Compute aggregate statistics: `total_input`, `total_output`, `fee_ratio = fee_btc / total_input`, `num_inputs`, `num_outputs`. |
| **Script type** | `script_type` | ✅ Yes | Categorical feature. |
| **Timestamps** | `timestamp`, `relay_timestamp` | ✅ Yes | Compute `propagation_delta_ms = (timestamp - relay_timestamp)` in milliseconds. Duration AUC in v3.0 is 0.5409 (safe from shortcut leakage). |
| **Network metadata** | `node_type`, `country_code`, `asn`, `isp` | ✅ Yes | 100% country overlap across 16 countries. Node types and ASNs are decorrelated and probabilistically shared. |
| **Group / Split** | `scenario_id`, `split` | ❌ Not features | Use `scenario_id` for group cross-validation. Use `split` for train/test evaluation. |
| **Labels / Leaked Props**| `is_illicit`, `pattern_type`, `is_licit_exchange` | 🚫 NEVER | Ground-truth targets and derived labels. Hard-exclude from feature matrix. |

---

## 9. Resolution of Known Limitations (v1.0 vs v2.0 vs v3.0 vs v4.0)

| # | Issue in v1.0 / v2.0 / v3.0 | v4.0 Status | Resolution Details in v4.0 |
|---|----------------------|-------------|----------------------------|
| 1 | **`time_span_hours` AUC = 1.000000** | ✅ **RESOLVED** | Licit scenarios restructured into realistic episodes (hours to weeks). Illicit spans hours to weeks. **Duration AUC reduced to 0.5409**; 89.9% distribution overlap. |
| 2 | **11,639-hour zero-overlap duration gap** | ✅ **RESOLVED** | Licit range: 0 to 2,136 hrs; Illicit range: 0 to 788 hrs. Overlap is continuous across all percentiles. |
| 3 | **`unique_asn_count` AUC = 0.999846** | ✅ **RESOLVED** | Expanded to 25 shared global ASNs across 16 countries. **ASN count AUC reduced to 0.6757**. |
| 4 | **Scenario-size proxy (`unique_ip_count` ~ `num_txns`)** | ✅ **RESOLVED** | Entity IP persistence implemented within scenarios. `num_txns` AUC is 0.5504; `unique_ip_count` AUC is 0.6521. |
| 5 | **Disjoint country codes** | ✅ **RESOLVED** | **100.0% overlap (16/16 shared countries)** across both classes. |
| 6 | **Tiny rare typology counts** | ✅ **RESOLVED** | **Scaled by 10x–25x**: peeling (2,915 txns / 260 scenarios), layering (2,058 txns / 260 scenarios), mixing (2,418 txns / 320 scenarios). |
| 7 | **Rigid typology topologies** | ✅ **RESOLVED** | Branching peeling chains, multi-source/multi-tier layering, pre-mix/post-mix CoinJoin clusters. |
| 8 | **Ransomware 1-txn artifact** | ✅ **RESOLVED** | Grouped into 2,043 multi-transaction campaigns (sizes 1–74 txns, durations up to 788 hrs). |
| 9 | **Train/test leakage** | ✅ **RESOLVED** | 100% leak-free scenario-level stratified split: `train ∩ test scenarios == 0`. |
| 10 | **Accounting identity** | ✅ **RESOLVED** | Strict UTXO accounting identity satisfied on 100% of rows (max residual = 0.00000000). |
| 11 | **Issue 6: Typology classification fingerprints** | ✅ **RESOLVED (v4)** | Decoupled correlated features (fanin_ratio, unique_input_addrs, etc.) by introducing multivalued generative archetypes. OVR AUCs all < 0.99. Dropping top feature causes real Macro-F1 delta. |

---

## 10. Changelog

| Version | Date | Author | Changes | Row Count Δ |
|---------|------|--------|---------|-------------|
| v1.0 | 2026-09-01 | P3 (Data Pipeline) | Initial release. Elliptic (46,564 rows) + Heist appended (25,000 rows). 1-input-1-output scalar format. | Baseline: 71,564 rows |
| v2.0 | 2026-09-02 | P3 (Data Pipeline) | Multi-I/O array columns, planted typologies (peeling, layering, mixing), hard-negative exchanges, `scenario_id` & deterministic 80/20 train/test split. Failed pre-ML diagnostic due to 11,639h duration shortcut (AUC=1.0) and ASN leak (AUC=0.9998). | +10,514 rows (82,078 rows) |
| v3.0 | 2026-09-03 | P3 (Data Pipeline) | Complete behavioral redesign: eliminated duration shortcut (AUC 0.5409, 89.9% overlap), resolved ASN/IP size proxies (entity IP persistence), scaled rare typologies (peeling: 2,915, mixing: 2,418, layering: 2,058), introduced structural diversity (branching peels, multi-tier layering, pre/post-mix CoinJoins), achieved 100% country overlap, zero leaking scenarios. Passes all 8 pre-ML acceptance gates (A–H) and 15 integrity checks. | +1,734 rows (Total: 83,812 rows) |
| v4.0 | 2026-09-04 | P3 (Data Pipeline) | Resolved Issue 6: Typology fingerprinting. Added custom structural noise injection (address reuse, dust sweeps, change splits) for peeling, layering, mixing, and ransomware. Decoupled correlated features and reduced OVR AUCs below 0.99. Validated that ablation of top feature costs Macro-F1. | +330 rows (Total: 84,142 rows) |

---

_End of data dictionary._
