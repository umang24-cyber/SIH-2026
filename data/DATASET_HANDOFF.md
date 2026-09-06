# 🚀 SIH 2026 — Bitcoin Forensics Dataset Handoff & ML Specification (v3.0)

This document provides a comprehensive technical overview of the synchronized multi-layer Bitcoin dataset generated for the **SIH 2026 Bitcoin Transaction Forensics & Network Analysis System**.

---

## 📌 Dataset Overview (v3.0)

- **Primary Join Key:** `txid` (64-bit integer, 100% 1:1 aligned across both layers)
- **Total Records:** `83,812` transactions across 6,031 scenario groups
- **Licit Transactions (`is_illicit = 0`):** `48,421` (57.77%) across 3,148 scenarios
- **Illicit Transactions (`is_illicit = 1`):** `35,391` (42.23%) across 2,883 scenarios
- **Data Period:** `2011-09-03` to `2018-11-17` (both licit and illicit span the entire timeframe)
- **Train Split (`split = 'train'`):** `68,334` transactions (4,824 scenarios, 42.2% illicit)
- **Test Split (`split = 'test'`):** `15,478` transactions (1,207 scenarios, 42.1% illicit)
- **Leak-Free Partitioning:** `train ∩ test scenarios == 0` (strict scenario-level stratification)

---

## 📁 Files & Schemas

The dataset is organized as a dual-layer synchronized architecture. Six CSV files are provided in `data/processed/`:
- Master files: `blockchain_transactions.csv`, `network_metadata.csv` (contain `split` and `scenario_id`)
- Pre-split files: `train_blockchain.csv`, `train_network.csv`, `test_blockchain.csv`, `test_network.csv`

### 1. `blockchain_transactions.csv` (On-Chain UTXO Ledger)
Contains the on-chain UTXO state with multi-input and multi-output arrays, financial values, script formats, and threat classification targets.

| Column | Type | Description | Example / Values |
|---|---|---|---|
| `txid` | `int64` | **Primary Key**: Hash-shuffled unique identifier for the Bitcoin transaction | `854009417` |
| `timestamp` | `datetime` | Block confirmation timestamp (floored to second) | `2016-11-18 04:04:51` |
| `input_addresses` | `JSON array[string]` | Base58 sender wallet addresses | `["1RUjgz6QLrFCTRHFvSrY3zqyvrAVDQ4"]` |
| `output_addresses` | `JSON array[string]` | Base58 receiver wallet addresses | `["11PvnHhjnfVCD4j4K3...", "1RaXwCiEP..."]` |
| `input_amounts` | `JSON array[float64]`| BTC input amounts per input address | `[0.27579544]` |
| `output_amounts` | `JSON array[float64]`| BTC output amounts per output address | `[0.17593553, 0.09978202]` |
| `fee_btc` | `float64` | Miner fee in BTC (`sum(input_amounts) - sum(output_amounts)`) | `0.00007789` |
| `script_type` | `string` | Bitcoin script format | `P2PKH`, `P2SH`, `P2WPKH`, `P2WSH` |
| `is_illicit` | `int` | Binary ground-truth target (`0` = Licit, `1` = Illicit/Threat) | `0` or `1` |
| `pattern_type` | `string` | Multiclass threat typology | `normal`, `ransomware`, `peeling_chain`, `layering`, `mixing` |
| `scenario_id` | `string` | Laundering campaign / cluster identifier | `licit_00001`, `peel_00042`, `mix_00010` |
| `split` | `string` | Pre-assigned partition | `train` or `test` |

### 2. `network_metadata.csv` (Off-Chain P2P Broadcast Telemetry)
Contains the P2P broadcast and network telemetry captured before block confirmation.

| Column | Type | Description | Example / Values |
|---|---|---|---|
| `txid` | `int64` | **Foreign Key**: Links 1:1 to `blockchain_transactions.csv` | `854009417` |
| `relay_timestamp` | `datetime` | P2P relay broadcast timestamp (guaranteed 50ms–500ms before `timestamp`) | `2016-11-18 04:04:50.562` |
| `relay_ip` | `string` | First-seen relay peer IPv4 address | `31.47.29.7` |
| `relay_port` | `int` | Peer connection port | `8333` (standard) or dynamic ports |
| `node_type` | `string` | Originating network infrastructure | `residential`, `datacenter`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`, `mobile` |
| `country_code` | `string` | ISO 3166-1 alpha-2 origin country code (100% licit/illicit overlap) | `US`, `DE`, `IN`, `RU`, `BZ`, `FR`, `JP`, `GB`, `AU`, etc. |
| `asn` | `string` | Autonomous System Number of the relay node (25 globally shared ASNs) | `AS15169`, `AS55836`, `AS210644`, `AS9009`, `AS1221`, etc. |
| `isp` | `string` | Internet Service Provider or hosting entity name | `Google LLC`, `Telstra Corporation`, `AEZA International`, etc. |
| `protocol_version`| `int` | Bitcoin protocol version | `70015` |
| `user_agent` | `string` | Client node software banner | `/Satoshi:22.0.0/`, `/Satoshi:21.1.0/`, `/btcd:0.22.0/` |
| `scenario_id` | `string` | Laundering campaign / cluster identifier | `licit_00001`, `peel_00042`, `mix_00010` |
| `split` | `string` | Pre-assigned partition | `train` or `test` |

---

## 🔬 Critical Structural Changes: Post-v2.0 Improvements & ML Impact

The v2.0 dataset suffered from severe structural artifacts that rendered ML models trivially overfitted (AUC = 1.000). The v3.0 release completely resolves these issues through behavioral re-generation:

### 1. Duration Shortcut Eliminated
- **v2.0 Issue:** Licit background scenarios were tens of thousands of hours long, while illicit scenarios were short (<115 hours). There was an 11,639-hour zero-overlap gap, giving `time_span_hours` AUC = 1.0000.
- **v3.0 Fix:** Licit background activity was segmented into realistic operational episodes (single transactions, hours, days, weeks). Illicit campaigns were extended to include slow-burn extortion and darknet operations (up to 788 hours).
- **ML Impact:** `duration_hrs` AUC dropped to **0.5409**, with **89.9% empirical distribution overlap**. The model must now learn topological and behavioral structure rather than thresholding time.

### 2. Scenario-Size & IP Collinearity Decoupled
- **v2.0 Issue:** `num_txns`, `unique_ip_count`, and `unique_input_addrs` were perfectly collinear proxies for scenario duration ($r \approx 0.99\text{--}1.0$), with licit scenarios having far more transactions by construction.
- **v3.0 Fix:** Implemented persistent entity IP reuse within scenarios; both licit and illicit distributions span small, medium, and large transaction counts (overlap > 81%).
- **ML Impact:** `num_txns` AUC is **0.5504** and `unique_ip_count` AUC is **0.6521**. No scenario-size feature can act as a binary shortcut.

### 3. Rare Typologies Scaled for Multiclass Evaluation
- **v2.0 Issue:** Peeling (309 rows / 40 scenarios), Layering (123 rows / 25 scenarios), and Mixing (90 rows / 20 scenarios) had insufficient rows for reliable evaluation (leaving ~18–60 test rows).
- **v3.0 Fix:** Scaled typologies by 10x–25x:
  - **Peeling chain:** 2,915 rows across 260 scenarios
  - **Layering:** 2,058 rows across 260 scenarios
  - **Mixing:** 2,418 rows across 320 scenarios
  - **Ransomware:** 28,000 rows across 2,043 campaigns
  - **Normal:** 48,421 rows across 3,148 scenarios
- **ML Impact:** Enables robust 5-class multi-class classification and per-typology test set metrics.

### 4. Structural Diversity within Typologies
- **v2.0 Issue:** Rigid templates (peeling was always 1-in-2-out; mixing was always equal-split 1-round).
- **v3.0 Fix:**
  - *Peeling chains:* 4–28 hops, variable decay rates, multi-input consolidation peels, and branching tree structures.
  - *Layering:* Multi-tier fan-out (3–12 outputs), intermediary sub-splits and pass-throughs, and multi-collector fan-ins.
  - *Mixing:* Pre-mix Tx0 splits, variable CoinJoin rounds (2–8 rounds), variable participants (3–8), and post-mix payout consolidations.
- **ML Impact:** Models must learn genuine topological graph patterns (e.g. GNNs, motif counts, fan-in/fan-out ratios) rather than matching rigid templates.

### 5. Categorical & Infrastructure Overlap
- **v2.0 Issue:** Country codes were partially disjoint; ASNs were not globally distributed.
- **v3.0 Fix:** 100% country code overlap across 16 countries (`US`, `DE`, `RU`, `NL`, `GB`, `IN`, `BZ`, `SC`, `FR`, `JP`, `AU`, `CA`, `SG`, `CH`, `BR`, `ZA`). 25 globally shared ASNs.
- **ML Impact:** Eliminates geo-categorical leakage; models learn probabilistic infrastructure risk rather than deterministic country filters.

### 6. Strict Ground-Truth Exclusions
- The columns `is_illicit`, `pattern_type`, and `is_licit_exchange` are strictly ground-truth labels and derived properties. **They must never be used as input features.**

---

## 🛠️ Role-Specific Implementation Guide

### 🤖 Machine Learning Engineer (P5)
1. **Train/Test Evaluation:** Always split by `scenario_id` using the provided `split` column (`train` vs `test`). Never perform random row-level splitting.
2. **Binary Classification:** Target is `is_illicit`. Combine UTXO transaction statistics, time-delta dynamics, network infrastructure probabilities, and graph embeddings.
3. **Multiclass Classification:** Target is `pattern_type` (`normal`, `ransomware`, `peeling_chain`, `layering`, `mixing`).
4. **Feature Safety:** Refer to section 8a of `DATA_DICTIONARY.md` for the explicit feature safety matrix.

### 🕸️ Graph Engineer (P4)
1. **Nodes:** `:Wallet {address}`, `:Transaction {txid, timestamp, fee_btc}`, `:IP {ip, asn, country_code, node_type}`.
2. **Edges:**
   - `(:Wallet)-[:SENT {amount_btc}]->(:Transaction)`
   - `(:Transaction)-[:RECEIVED {amount_btc}]->(:Wallet)`
   - `(:IP)-[:BROADCASTED {relay_timestamp, port, user_agent}]->(:Transaction)`
3. **Graph Algorithms:** Community detection, PageRank, fan-in/fan-out motif analysis, and pass-through path discovery.

---

*See [DATA_DICTIONARY.md](file:///home/param/SIH-2026/DATA_DICTIONARY.md) for full field-level specifications and [V3_ACCEPTANCE_AUDIT.md](file:///home/param/SIH-2026/V3_ACCEPTANCE_AUDIT.md) for diagnostic audit verification.*
