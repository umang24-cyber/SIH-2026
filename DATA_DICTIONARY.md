# DATA_DICTIONARY.md — SIH PS 146 Bitcoin AML Dataset

> **Audience:** P4 (Graph Engineer) and P5 (ML Engineer).
> **Last updated:** 2026-09-02 · Data version **v2.0**.

---

## 1. File Inventory

| File | Path | Format | Rows | Size | One-line description |
|------|------|--------|------|------|----------------------|
| `blockchain_transactions.csv` | `data/processed/blockchain_transactions.csv` | CSV (UTF-8, comma-delimited) | 82,078 | ~18 MB | Master on-chain ledger: UTXO array inputs/outputs, BTC amounts, miner fees, script types, ground-truth labels, typology patterns, scenario IDs, and train/test split tags. |
| `network_metadata.csv` | `data/processed/network_metadata.csv` | CSV (UTF-8, comma-delimited) | 82,078 | ~10 MB | Master P2P broadcast telemetry: relay timestamps, relay IPs, ports, decorrelated node types, ASNs, ISPs, user agents, scenario IDs, and split tags. |
| `train_blockchain.csv` | `data/processed/train_blockchain.csv` | CSV | 65,659 | ~14 MB | Pre-split train set (80%) of `blockchain_transactions.csv`. |
| `train_network.csv` | `data/processed/train_network.csv` | CSV | 65,659 | ~8 MB | Pre-split train set (80%) of `network_metadata.csv`. |
| `test_blockchain.csv` | `data/processed/test_blockchain.csv` | CSV | 16,419 | ~4 MB | Pre-split test set (20%) of `blockchain_transactions.csv`. |
| `test_network.csv` | `data/processed/test_network.csv` | CSV | 16,419 | ~2 MB | Pre-split test set (20%) of `network_metadata.csv`. |

Both master files (and their corresponding split files) are **row-aligned on `txid`** — row _N_ in one file corresponds to the same transaction as row _N_ in the other after a join (always join on `txid`).

---

## 2. Field-by-Field Dictionary

### 2a. `blockchain_transactions.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Unitless 64-bit integer ID | No | `58234917` | Unique transaction identifier. Generated via hash salt shuffling to eliminate ID range leakage. |
| 2 | `timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS` (UTC) | No | `2014-03-15 09:22:41` | Block-confirmation timestamp. Range: 2011–2018 (extended for both licit and illicit rows). |
| 3 | `input_addresses` | `object` (JSON array string) | Array of Base58 strings | No | `["12dhqUGwz..."]` | Array of 1–10 input Bitcoin addresses (UTXO senders). |
| 4 | `output_addresses` | `object` (JSON array string) | Array of Base58 strings | No | `["1EcgU6KKS...", "1PZDhrao8..."]` | Array of 1–10 output Bitcoin addresses (UTXO recipients). Includes wallet reuse for multi-hop graph connectivity. |
| 5 | `input_amounts` | `object` (JSON array string) | Array of floats (BTC) | No | `[0.26361416]` | Array of input BTC amounts corresponding 1:1 with `input_addresses`. |
| 6 | `output_amounts` | `object` (JSON array string) | Array of floats (BTC) | No | `[0.0526, 0.21066308]` | Array of output BTC amounts corresponding 1:1 with `output_addresses`. |
| 7 | `fee_btc` | `float64` | BTC, 8 decimal places | No | `0.00035108` | Miner fee. Satisfies accounting identity: `sum(input_amounts) = sum(output_amounts) + fee_btc`. |
| 8 | `script_type` | `object` (string) | Categorical enum | No | `P2PKH` | Bitcoin output script type: `P2PKH` (45%), `P2SH` (25%), `P2WPKH` (25%), `P2WSH` (5%). |
| 9 | `is_illicit` | `int64` | Binary: `0` = licit, `1` = illicit | No | `0` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Target variable. |
| 10 | `pattern_type` | `object` (string) | Categorical enum | No | `peeling_chain` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Values: `normal`, `ransomware`, `peeling_chain`, `layering`, `mixing`. |
| 11 | `scenario_id` | `object` (string) | Identifier string | No | `peel_001` | Grouping key for leak-free train/test splitting. |
| 12 | `split` | `object` (string) | Categorical: `train` or `test` | No | `train` | Deterministic 80/20 scenario-level split tag. |

#### Array-Valued Fields
In v2.0, transactions are real multi-input / multi-output UTXO transactions. Columns `input_addresses`, `output_addresses`, `input_amounts`, and `output_amounts` are serialized JSON arrays. Parse them using `json.loads()`.

---

### 2b. `network_metadata.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Foreign key to `blockchain_transactions.csv` | No | `58234917` | Transaction ID mapping 1:1 to the blockchain ledger file. |
| 2 | `relay_timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS.mmm` (UTC) | No | `2014-03-15 09:22:40.812` | P2P broadcast timestamp. Guaranteed strictly 50–500 ms prior to block `timestamp`. |
| 3 | `relay_ip` | `object` (string) | IPv4 dotted-quad | No | `38.148.127.142` | Synthetically generated origin peer IPv4 address. |
| 4 | `relay_port` | `int64` | TCP port number | No | `8333` | Origin port (85% standard port `8333`, 15% dynamic/alt ports). |
| 5 | `node_type` | `object` (string) | Categorical enum | No | `residential` | Infrastructure classification. Overlapping pools: `residential`, `datacenter`, `mobile`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`. |
| 6 | `country_code` | `object` (string) | ISO 3166-1 alpha-2 | No | `IN` | Country code associated with the relay ASN. |
| 7 | `asn` | `object` (string) | `AS` prefix + number | No | `AS55836` | Autonomous System Number. 15 distinct ASNs total. |
| 8 | `isp` | `object` (string) | Org name string | No | `Reliance Jio Infocomm` | ISP / network infrastructure provider name. |
| 9 | `protocol_version` | `int64` | Bitcoin protocol version | No | `70015` | Constant `70015`. |
| 10 | `user_agent` | `object` (string) | Bitcoin client banner | No | `/Satoshi:22.0.0/` | Node software identifier string. |
| 11 | `scenario_id` | `object` (string) | Grouping string | No | `peel_001` | Identical to `scenario_id` in blockchain file. |
| 12 | `split` | `object` (string) | Categorical enum | No | `train` | Identical to `split` in blockchain file. |

---

## 3. Ground Truth / Labels

### Label Columns

| Column | Role | Values | Distribution |
|--------|------|--------|--------------|
| `is_illicit` | **Binary class label** | `0` (licit), `1` (illicit) | 52,011 licit (63.4%) / 30,067 illicit (36.6%) |
| `pattern_type` | **Multi-class typology label** | `normal`, `ransomware`, `peeling_chain`, `layering`, `mixing` | • `normal`: 52,011<br>• `ransomware`: 29,545<br>• `peeling_chain`: 309<br>• `layering`: 123<br>• `mixing`: 90 |

### ⚠️ Feature Exclusion List (P5 must hard-drop these before training)

```
is_illicit
pattern_type
```

---

## 4. Scenario Identifiers & Train/Test Split

`scenario_id` groups all transactions and wallets belonging to the same laundering pattern, ransomware campaign, exchange cluster, or background activity group.

### Deterministic 80/20 Split Rules
- **Stratified Group Split**: Split performed at scenario level (`test_size=0.2`, `random_state=42`) stratified by `(is_illicit, pattern_type)`.
- **Zero Leakage**: 100% of transactions for any given `scenario_id` reside strictly in `train` or `test`, never both.
- **Stratification Result**:
  - `train`: 65,659 rows (36.6% illicit) across 14,090 scenarios.
  - `test`: 16,419 rows (36.6% illicit) across 3,523 scenarios.

---

## 5. Hard Negatives

To prevent models from relying on simple wallet transaction counts as a perfect illicit separator, v2.0 plants **30 synthetic high-activity licit exchange wallets**:
- Each exchange wallet processes **50 to 500 transactions** (totaling 9,992 transactions).
- Exhibits real exchange topology shapes (fan-out withdrawals and fan-in deposits).
- All exchange transactions are marked with `is_illicit = 0` and `pattern_type = normal`.

---

## 6. Join / Integrity Validation Report

All 15 automated integrity checks in `data_pipeline/validate_v2.py` pass 100%:

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | Row Count Match | ✅ PASS | Blockchain: 82,078 \| Network: 82,078 |
| 2 | Key Alignment | ✅ PASS | 0 orphan txids in either direction |
| 3 | Duplicate txids | ✅ PASS | 0 duplicates across all 82,078 rows |
| 4 | Timing Logic | ✅ PASS | 0 violations (`relay_timestamp <= timestamp`) |
| 5 | Null Values | ✅ PASS | 0 null values across all columns in both files |
| 6 | Array Column Parsing | ✅ PASS | Valid JSON, length of addresses == length of amounts |
| 7 | Accounting Identity | ✅ PASS | `sum(inputs) = sum(outputs) + fee` (max residual 0.00000000) |
| 8 | Typology Distribution | ✅ PASS | All 5 pattern_types present (`normal`, `ransomware`, `peeling_chain`, `layering`, `mixing`) |
| 9 | Scenario_id Coverage | ✅ PASS | 100% non-null coverage across 17,613 distinct scenario IDs |
| 10 | Hard Negatives | ✅ PASS | 30 licit exchange wallets with ≥50 transactions each |
| 11 | Network Decorrelation | ✅ PASS | Overlapping pools: suspicious types in licit, normal in illicit |
| 12 | Txid Uniformity | ✅ PASS | Hash-shuffled IDs; max illicit concentration in 500-txid window = 42.0% |
| 13 | Timestamp Overlap | ✅ PASS | Both licit and illicit rows span 2011–2016 and 2017–2018 |
| 14 | Split Integrity | ✅ PASS | 0 leaking scenarios between train and test splits |
| 15 | Split Stratification | ✅ PASS | Train illicit %: 36.6%, Test illicit %: 36.6% (diff: 0.1pp) |

---

## 7. Graph Construction Notes (for P4)

### 7a. Node Types

| Node Type | Key | Properties |
|-----------|-----|------------|
| **Wallet** | `address` (string) | `is_licit_exchange` (derived from high degree + licit label) |
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
- **Peeling chains**: 1 input → 2 outputs (peeled payment + change output). Change output address is reused as input for the next hop.
- **Layering**: 1 input → N outputs (fan-out), followed by N inputs → 1 output (fan-in).
- **Mixing**: N inputs → N equal-value outputs across multiple rounds (CoinJoin pattern).

---

## 8. ML-Ready Notes (for P5)

### 8a. Feature Safety Matrix

| Category | Columns | Safe as Direct Features? | Notes |
|----------|---------|--------------------------|-------|
| **Transaction amounts** | `input_amounts`, `output_amounts`, `fee_btc` | ✅ Yes | Compute aggregate statistics: `total_input`, `total_output`, `fee_ratio = fee_btc / total_input`, `num_inputs`, `num_outputs`. |
| **Script type** | `script_type` | ✅ Yes | Categorical feature. |
| **Timestamps** | `timestamp`, `relay_timestamp` | ✅ Yes | Compute `propagation_delta_ms = (timestamp - relay_timestamp)` in milliseconds. Extract time features. |
| **Network metadata** | `node_type`, `country_code`, `asn`, `isp` | ✅ Yes | In v2.0, pools overlap (14.9% of licit rows use suspicious infrastructure; 19.7% of illicit rows use normal infrastructure). Safe to use without artificial leakage. |
| **Group / Split** | `scenario_id`, `split` | ❌ Not features | Use `scenario_id` for group cross-validation. Use `split` for train/test evaluation. |
| **Labels** | `is_illicit`, `pattern_type` | 🚫 NEVER | Ground-truth targets. Hard-exclude from feature matrix. |

---

## 9. Resolution of Known Limitations (v1.0 vs v2.0)

| # | Issue in v1.0 | v2.0 Status | Resolution Details |
|---|---------------|-------------|--------------------|
| 1 | **No typology sub-labels** | ✅ **RESOLVED** | Planted structurally distinct peeling chains (309 txns), layering clusters (123 txns), and mixing clusters (90 txns). `pattern_type` now contains 5 classes. |
| 2 | **No `scenario_id` column** | ✅ **RESOLVED** | Added `scenario_id` to both master files and emitted pre-stratified 80/20 train/test split files (`train_*.csv`, `test_*.csv`). |
| 3 | **No hard negatives** | ✅ **RESOLVED** | Injected 30 exchange-like licit wallets with 50–500 txns each (9,992 total transactions). High activity is no longer a perfect separator. |
| 4 | **Network metadata deterministic on label** | ✅ **RESOLVED** | Overlapped reference pools: 14.9% of licit transactions use VPN/Tor/suspicious ASNs, and 19.7% of illicit transactions use residential/datacenter/normal ASNs. |
| 5 | **1-input-1-output only** | ✅ **RESOLVED** | Converted to real multi-input / multi-output UTXO structure using array columns (`input_addresses[]`, `output_addresses[]`, `input_amounts[]`, `output_amounts[]`). |
| 6 | **`output_wallet` always unique** | ✅ **RESOLVED** | Added UTXO output pool reuse, enabling multi-hop receive-side and pass-through chain graph analysis. |
| 7 | **`txid` range leaks label** | ✅ **RESOLVED** | All txids assigned via hash-salt shuffling. Label concentration in any 500-txid window is capped at ~42%. |
| 8 | **Timestamp source leak** | ✅ **RESOLVED** | Extended licit timestamps back to 2011–2016 (10,402 licit rows backdated). Both classes now span 2011–2018. |

---

## 10. Changelog

| Version | Date | Author | Changes | Row Count Δ |
|---------|------|--------|---------|-------------|
| v1.0 | 2026-09-01 | P3 (Data Pipeline) | Initial release. Elliptic (46,564 rows) + Heist appended (25,000 rows). 1-input-1-output scalar format. | Baseline: 71,564 rows |
| v2.0 | 2026-09-02 | P3 (Data Pipeline) | Full redesign: multi-I/O array columns, planted typologies (peeling, layering, mixing), hard-negative exchanges, `scenario_id` & deterministic 80/20 train/test split, network metadata pool decorrelation, hash-shuffled txids, and 2011–2016 licit timestamp extension. Passes 15/15 integrity checks. | +10,514 rows (Total: 82,078 rows) |

---

_End of data dictionary._
