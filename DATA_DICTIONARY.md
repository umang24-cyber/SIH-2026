# DATA_DICTIONARY.md — SIH PS 146 Bitcoin AML Dataset

> **Audience:** P4 (Graph Engineer) and P5 (ML Engineer).
> **Last updated:** 2026-09-01 · Data version **v1.0**.

---

## 1. File Inventory

| File | Path | Format | Rows | Size | One-line description |
|------|------|--------|------|------|----------------------|
| `blockchain_transactions.csv` | `data/processed/blockchain_transactions.csv` | CSV (UTF-8, comma-delimited) | 71 564 | 9.0 MB | On-chain ledger: wallets, amounts, fees, script types, and ground-truth illicit/licit labels. |
| `network_metadata.csv` | `data/processed/network_metadata.csv` | CSV (UTF-8, comma-delimited) | 71 564 | 8.2 MB | Synthesized P2P broadcast telemetry: relay IPs, ports, node types, ASNs, ISPs, user agents. |

Both files are **row-aligned on `txid`** — row _N_ in one file corresponds to the same transaction as row _N_ in the other after a join (though physical row order may differ; always join on `txid`).

---

## 2. Field-by-Field Dictionary

### 2a. `blockchain_transactions.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Unitless integer ID | No | `245355036` | Unique transaction identifier (Elliptic dataset IDs for original 46 564 rows; synthetic sequential `999000001–999025000` for the 25 000 appended heist rows). |
| 2 | `timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS` (no timezone; treat as UTC) | No | `2017-01-29 18:27:29` | Block-confirmation timestamp. Derived from Elliptic `time_step` × 14-day windows + random jitter (0–14 days). |
| 3 | `input_wallet` | `object` (string) | Base58 Bitcoin address, 26–34 chars, starts with `1` | No | `12dhqUGwz1W5PogMP6LjgisGzg9Z4` | Sending wallet. **Illicit rows:** real addresses from the Bitcoin Heist ransomware dataset. **Licit rows:** synthetically generated Base58 strings. |
| 4 | `output_wallet` | `object` (string) | Base58 Bitcoin address, 26–34 chars, starts with `1` | No | `1EcgU6KKSdjtWmXzy5W3EX34ibCoH` | Receiving wallet. Always synthetically generated. Every `output_wallet` value is globally unique (71 564 distinct values). |
| 5 | `amount_btc` | `float64` | BTC (not satoshis), 8 decimal places | No | `0.26326308` | Transfer amount. Log-normal distribution (μ=−2.0, σ=1.5), clipped at 1e-8. Range: 0.000106–89.01 BTC; mean 0.41 BTC. |
| 6 | `fee_btc` | `float64` | BTC (not satoshis), 8 decimal places | No | `0.00035108` | Miner fee. Uniform distribution U(0.00001, 0.0005). |
| 7 | `script_type` | `object` (string) | Categorical enum | No | `P2PKH` | Bitcoin output script type. Values: `P2PKH` (45%), `P2SH` (25%), `P2WPKH` (25%), `P2WSH` (5%). Randomly assigned; **not** correlated with `is_illicit`. |
| 8 | `is_illicit` | `int64` | Binary: `0` = licit, `1` = illicit | No | `0` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Source: Elliptic class labels (class 1 → illicit, class 2 → licit). |
| 9 | `pattern_type` | `object` (string) | Categorical enum | No | `ransomware` | **⚠️ GROUND-TRUTH LABEL — do not use as a feature.** Values in the current data: `normal` (all licit rows) and `ransomware` (all illicit rows). See §3 for details. |

#### Array-Valued Fields

**There are none.** Each row represents a single input→output transfer with scalar `input_wallet`, `output_wallet`, `amount_btc`, and `fee_btc`. There are no `input_addresses[]`, `output_addresses[]`, `input_amounts[]`, or `output_amounts[]` array columns. Multi-input / multi-output UTXO fan-in / fan-out is **not** modeled at the row level — each row is one edge of the transaction. If a real Bitcoin transaction had 3 inputs and 2 outputs, it would appear as multiple rows with the same `txid` in a real dataset, but **in this dataset every `txid` is unique** (71 564 distinct values, 0 duplicates). This means each row is effectively a 1-input-1-output transfer.

---

### 2b. `network_metadata.csv`

| # | Column | dtype | Units / Format | Nullable? | Example | Meaning |
|---|--------|-------|----------------|-----------|---------|---------|
| 1 | `txid` | `int64` | Same ID space as blockchain file | No | `245355036` | Foreign key to `blockchain_transactions.csv`. |
| 2 | `relay_timestamp` | `object` (string) | `YYYY-MM-DD HH:MM:SS.mmm` (millisecond precision, no timezone; treat as UTC) | No | `2017-01-29 18:27:28.694` | Timestamp when the relay node first broadcast the transaction on the P2P network. Always **50–500 ms before** the corresponding `timestamp` in the blockchain file. |
| 3 | `relay_ip` | `object` (string) | IPv4 dotted-quad | No | `38.148.127.142` | **Broadcasting node's IP address** — the peer that first relayed this transaction into the mempool. See IP semantics below. |
| 4 | `relay_port` | `int64` | TCP port number | No | `8333` | Source port of the broadcasting peer. 85% are the standard Bitcoin port `8333`; 15% are dynamic/alt ports (`18333` or `49152–65472`). |
| 5 | `node_type` | `object` (string) | Categorical enum | No | `residential` | Infrastructure classification of the broadcasting node. Values: `residential`, `datacenter`, `mobile`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`. |
| 6 | `country_code` | `object` (string) | ISO 3166-1 alpha-2 | No | `IN` | Country code assigned to the relay node based on the ASN pool it was drawn from (not a GeoIP lookup of `relay_ip`). |
| 7 | `asn` | `object` (string) | `AS` prefix + number | No | `AS55836` | Autonomous System Number of the relay node's network. 15 distinct ASNs total (8 normal, 7 suspicious). |
| 8 | `isp` | `object` (string) | Free-text org name | No | `Reliance Jio Infocomm` | ISP / hosting provider name associated with the ASN. 15 distinct values. |
| 9 | `protocol_version` | `int64` | Bitcoin protocol version integer | No | `70015` | Always `70015` in this dataset (constant column). |
| 10 | `user_agent` | `object` (string) | Bitcoin client banner string | No | `/Satoshi:22.0.0/` | Node software identifier. 4 values: `/Satoshi:22.0.0/` (55%), `/Satoshi:21.1.0/` (25%), `/Satoshi:0.20.1/` (15%), `/btcd:0.22.0/` (5%). |

#### `relay_ip` / `dst_ip` Semantics

- **`relay_ip` = the broadcasting node** (the peer that injected the transaction into the P2P gossip network). There is no `dst_ip` column; only the source/origin side is recorded.
- **NAT:** IPs are synthetically generated public IPv4 addresses (first octet 11–223, excluding reserved ranges). They do **not** reflect real-world NAT; each row gets a fresh random IP.
- **Tor exit nodes:** Tor-flagged rows (`node_type = tor_exit_node`) receive a **real-looking public IPv4 address**, not a placeholder like `0.0.0.0`. The Tor nature is indicated by `node_type`, `asn` (typically `AS200052`), and `isp` (`Tor-Relay-Network`). You cannot identify Tor usage from the IP alone.
- **VPN proxies:** Same treatment — real-looking IP, identified only via `node_type = vpn_proxy`.

---

## 3. Ground Truth / Labels

### Label Columns

| Column | Role | Values | Count |
|--------|------|--------|-------|
| `is_illicit` | **Binary class label** | `0` (licit), `1` (illicit) | 42 019 licit / 29 545 illicit |
| `pattern_type` | **Typology label** | `normal`, `ransomware` | 42 019 normal / 29 545 ransomware |

### ⚠️ Feature Exclusion List (P5 must hard-drop these before training)

```
is_illicit
pattern_type
```

These two columns are the **only** label columns. They must **never** appear in the feature matrix, the graph embedding input, or any derived feature. Hard-exclude them by name in your preprocessing pipeline.

### Typology Sub-Labels

**No sub-typology labels exist in the current data.** The generation script contains dead-code paths for `layering`, `mixing`, and `chain_hop` sub-types, but they are never triggered because every illicit row receives a Bitcoin Heist ransomware address (which forces `pattern_type = ransomware`). In the final data:

- `is_illicit = 0` ↔ `pattern_type = normal` (42 019 rows, 100% overlap)
- `is_illicit = 1` ↔ `pattern_type = ransomware` (29 545 rows, 100% overlap)

`pattern_type` is therefore a **redundant encoding of `is_illicit`** and carries zero additional information. Do not build a multi-class typology classifier against this field in its current state — it collapses to binary. See §9 for planned changes.

---

## 4. Scenario / Group Identifiers

### ⚠️ No scenario_id or group column exists.

There is no column that groups transactions belonging to the same planted laundering scenario, ransomware campaign, or wallet cluster.

**Why this matters (P5):** If you split train/val/test at the row level, transactions from the same ransomware wallet will leak across splits (the same `input_wallet` appears in up to 306 transactions). You **must** split at the `input_wallet` level at minimum:

```python
from sklearn.model_selection import GroupShuffleSplit
splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=df['input_wallet']))
```

**Recommendation:** P3 should add a `scenario_id` column that clusters related wallets/transactions into laundering scenarios. Until then, use `input_wallet` as the group key for splitting.

---

## 5. Hard Negatives

### ⚠️ No dedicated hard-negative column or marker exists.

There are **no** legitimate-but-high-activity "exchange-like" wallets planted in the data. Every licit `input_wallet` appears in exactly **1 transaction** (0 licit wallets have ≥ 2 txns). All high-activity wallets (≥ 2 txns from the same `input_wallet`) are illicit — the top wallet has 306 transactions.

**Consequence:** A trivial feature like `count(txns per input_wallet)` will perfectly separate illicit from licit. This is a **data artifact, not a real signal**. P5 must be aware that:

1. Models will overfit to wallet-frequency features unless hard negatives are added.
2. Hard negatives are currently identifiable **only by their absence** — there is no column to filter on.

**Recommendation:** P3 should inject synthetic high-activity licit wallets (exchange-like fan-out/fan-in with 50–500 txns each, `is_illicit = 0`) before P5 begins feature engineering.

---

## 6. Join / Integrity Notes

All checks below were validated by [`validate_pipeline.py`](data_pipeline/validate_pipeline.py).

| Check | Result |
|-------|--------|
| `txid` join type | **1:1** — every txid in one file has exactly one match in the other. |
| Orphan txids (in blockchain only) | **0** |
| Orphan txids (in network only) | **0** |
| Duplicate txids (blockchain) | **0** (71 564 unique) |
| Duplicate txids (network) | **0** (71 564 unique) |
| Null values (blockchain) | **0** across all 9 columns |
| Null values (network) | **0** across all 10 columns |
| Timing violations (`relay_timestamp > timestamp`) | **0** |
| Propagation delta range | **50–500 ms** (mean 274 ms, uniform distribution) |

### If a future data refresh breaks this:

1. Re-run `python data_pipeline/validate_pipeline.py` — it performs all 5 checks and reports pass/fail.
2. If orphans appear: decide whether to inner-join (drop orphans) or investigate the pipeline step that dropped rows.
3. If timing violations appear: the `relay_timestamp` generation in `step5_build_network_metadata.py` (line 105-106) subtracts `U(50,500)` ms from `timestamp` — check that the subtraction didn't overflow on edge-case timestamps.

---

## 7. Graph Construction Notes (for P4)

### 7a. Node Types

Derive three node types from the raw columns:

| Node Type | Source Column(s) | Key | Properties |
|-----------|-----------------|-----|------------|
| **Wallet** | `input_wallet`, `output_wallet` | `address` (string) | — |
| **Transaction** | `txid` | `txid` (int64) | `timestamp`, `amount_btc`, `fee_btc`, `script_type` |
| **IP** | `relay_ip` | `address` (string) | `country_code`, `asn`, `isp`, `node_type`, `relay_port` |

### 7b. Edge Types

| Edge | Direction | Source Columns | Properties |
|------|-----------|---------------|------------|
| **SENT** | `Wallet → Transaction` | `input_wallet` → `txid` | `amount_btc`, `fee_btc` |
| **RECEIVED** | `Transaction → Wallet` | `txid` → `output_wallet` | `amount_btc` |
| **BROADCAST** | `IP → Transaction` | `relay_ip` → `txid` | `relay_timestamp`, `relay_port`, `protocol_version`, `user_agent` |

Wallet-to-wallet transfer edges can be derived transitively: `input_wallet --SENT--> txid --RECEIVED--> output_wallet`.

### 7c. Multi-Input / Multi-Output Representation

**This dataset does not have multi-input or multi-output transactions.** Every `txid` appears exactly once, with one `input_wallet` and one `output_wallet`. The Transaction node is therefore always degree-1 on both the SENT and RECEIVED edges.

If you want to model fan-in / fan-out:
- **Fan-in:** Multiple rows with **different** `input_wallet` values that share the same `output_wallet`. In this dataset, every `output_wallet` is unique, so there is **no fan-in at the output side**. However, the same `input_wallet` sends to many different `output_wallet` values (fan-out from the sender perspective).
- **Fan-out:** A single `input_wallet` appearing in multiple rows (multiple Transaction nodes). This exists for illicit wallets (up to 306 txns from one wallet) but not for licit wallets (all have exactly 1 txn).

**Do not collapse multiple edges into a single aggregate edge** — keep each Transaction as a separate node to preserve temporal ordering and amount granularity.

### 7d. GeoIP / ASN Resolution

The `country_code`, `asn`, and `isp` fields are **pre-assigned** in the CSV based on hardcoded ASN pools in the generation script (8 normal ASNs + 7 suspicious ASNs). They are **not** derived from a GeoIP lookup of `relay_ip`.

- **There is no GeoLite2 database or runtime GeoIP call.** The `relay_ip` values are randomly generated and do not correspond to the stated `country_code` / `asn`.
- If you need real GeoIP resolution in production, use MaxMind's GeoLite2 City/ASN databases (local `.mmdb` files) with the `geoip2` Python library. Do not call external APIs at query time.
- For this dataset: **trust the `country_code`, `asn`, `isp` columns directly**; do not re-resolve from `relay_ip`.

---

## 8. ML-Ready Notes (for P5)

### 8a. Feature Safety Matrix

| Category | Columns | Safe as Direct Features? | Notes |
|----------|---------|--------------------------|-------|
| **Transaction amounts** | `amount_btc`, `fee_btc` | ✅ Yes | Per-row scalar values. Compute `fee_ratio = fee_btc / amount_btc` as a derived feature. |
| **Script type** | `script_type` | ✅ Yes | One-hot or label encode. 4 categories. Not correlated with `is_illicit` (randomly assigned). |
| **Timestamps** | `timestamp`, `relay_timestamp` | ✅ Yes | Compute `propagation_delta_ms = (timestamp - relay_timestamp)` as a feature. Also extract hour-of-day, day-of-week. |
| **Network metadata** | `node_type`, `country_code`, `asn`, `isp`, `user_agent`, `relay_port` | ⚠️ Use with caution | These are **strongly correlated with the label by construction**: illicit rows draw from suspicious ASN/node_type pools, licit from normal pools. A model trained on these will achieve high accuracy but learn the synthetic generation rule, not real AML signals. See §8d. |
| **Wallet addresses** | `input_wallet`, `output_wallet` | ❌ Not directly | Raw string addresses should not be used as features. Derive graph-aggregated features: in-degree, out-degree, tx-count-per-wallet, mean-amount-per-wallet, temporal-burst-rate. |
| **IP addresses** | `relay_ip` | ❌ Not directly | Randomly generated; no real geographic or network information. Use `asn`, `country_code`, `node_type` instead. |
| **Protocol version** | `protocol_version` | ❌ Useless | Constant `70015` for all rows. Zero variance → drop it. |
| **Labels** | `is_illicit`, `pattern_type` | 🚫 NEVER | Ground-truth targets. Hard-exclude from all feature sets. |

### 8b. Features Requiring Graph-Derived Aggregation

These features cannot be computed from a single row and require multi-row traversal or graph construction first:

| Feature | Computation | Why it matters |
|---------|-------------|----------------|
| Wallet tx count | `COUNT(txid) GROUP BY input_wallet` | Wallet activity volume (but see §5 — currently a perfect separator). |
| Wallet total volume | `SUM(amount_btc) GROUP BY input_wallet` | Total BTC moved by a wallet. |
| Wallet temporal spread | `MAX(timestamp) - MIN(timestamp) GROUP BY input_wallet` | Burst vs. sustained activity. |
| Chain length / decay rate | Multi-hop traversal: `input_wallet → output_wallet → next input_wallet → ...` | Requires building the wallet transfer graph. Not directly computable from flat rows because `output_wallet` values are all unique (no chaining exists in current data). |
| IP fan-out | `COUNT(DISTINCT txid) GROUP BY relay_ip` | Nearly all IPs are unique (71 519 / 71 564), so this is ~1 for all rows. Low utility. |

### 8c. Class Balance

| Split | Licit (0) | Illicit (1) | Ratio |
|-------|-----------|-------------|-------|
| **Overall** | 42 019 (58.7%) | 29 545 (41.3%) | ~1.42:1 |

- The ~59/41 split holds **only in aggregate**. There are no scenario groups to verify within-scenario balance.
- `pattern_type` is perfectly correlated with `is_illicit` (normal ↔ 0, ransomware ↔ 1), so within-pattern balance is trivially 100%/0%.

### 8d. Synthetic Artifacts / Potential Leak-y Shortcut Features

> **⚠️ Read this section carefully before feature engineering.**

| Artifact | Description | Leakage Risk |
|----------|-------------|--------------|
| **`node_type` is deterministic on label** | Licit rows draw from `{residential, datacenter, mobile}`; illicit from `{tor_exit_node, vpn_proxy, bulletproof_host, residential}`. The types `tor_exit_node`, `vpn_proxy`, `bulletproof_host` appear **only** in illicit rows (100% precision). `datacenter` and `mobile` appear **only** in licit rows. | 🔴 **High.** A one-hot on `node_type` gives near-perfect classification. This is a generation artifact. |
| **`asn` / `isp` pools are split by label** | 8 ASNs are used only for licit rows, 7 ASNs only for illicit. Zero overlap. | 🔴 **High.** Same issue as `node_type`. |
| **`country_code` partially split** | `US`, `NL`, `JP`, `FR`, `IN` appear only in licit rows. `SC`, `BZ`, `RO`, `DE`, `GB`, `RU` include illicit rows. Some countries (like `DE`, `RU`) are used for both suspicious ASNs. | 🟡 **Medium.** |
| **Wallet reuse asymmetry** | All licit `input_wallet` values appear exactly once; illicit wallets reuse addresses (up to 306 times). | 🔴 **High.** `tx_count_per_wallet > 1` ⟹ illicit with 100% precision. |
| **`txid` range** | Synthetic heist rows use `txid ∈ [999000001, 999025000]` — a contiguous block at the top of the ID space. Elliptic illicit txids have no such pattern. | 🟡 **Medium.** A feature like `txid > 999000000` catches 25k/29.5k illicit rows. |
| **Timestamp source** | Elliptic rows: 2017-01-01 to 2018-11-17 (14-day bins + jitter). Heist-appended rows: 2011-09-03 to 2018-10-30 (from BitcoinHeist `year`+`day` fields). Licit rows are exclusively from Elliptic (post-2017). | 🟡 **Medium.** `timestamp < 2017` ⟹ illicit with high probability. |
| **`protocol_version`** | Constant `70015`. | ✅ None (zero variance → auto-dropped). |
| **Missing values** | Zero nulls across all columns in both files. | ✅ None. |
| **Propagation delta** | Uniformly distributed 50–500 ms, independent of `is_illicit`. | ✅ None (not correlated with label). |

### 8e. Recommended Approach

1. **Baseline:** Train on `amount_btc`, `fee_btc`, `fee_ratio`, `script_type`, `propagation_delta_ms`, `hour_of_day`, `day_of_week` only. These are label-independent features.
2. **Graph-augmented:** Add graph-derived wallet-level and IP-level aggregations from P4's graph.
3. **Ablation:** Explicitly test with and without `node_type`, `asn`, `country_code` to measure how much accuracy is real vs. synthetic artifact.

---

## 9. Known Limitations / Open Questions

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| 1 | **No typology sub-labels.** `pattern_type` only contains `normal`/`ransomware`. The generation script has dead code for `layering`, `mixing`, `chain_hop` that never executes. P5 cannot build a multi-class typology classifier. | Blocks multi-class classification task. | 🔲 **Needs fix in `step4_build_blockchain_table.py`** — the `heist_label` assignment in sub-task 3 covers all illicit rows, so the random typology assignment in sub-task 4 (lines 218-225) never triggers. |
| 2 | **No `scenario_id` column.** No way to group related transactions into laundering scenarios for proper train/test splitting. | Risk of data leakage in evaluation. | 🔲 **Needs to be added** — cluster wallets into campaigns (e.g., by shared `input_wallet` + temporal proximity). |
| 3 | **No hard negatives.** All high-activity wallets are illicit. A trivial frequency feature achieves perfect separation. | Model will not generalize to real exchanges/services. | 🔲 **Needs synthetic exchange-like licit wallets** with 50–500 txns each. |
| 4 | **Network metadata is label-deterministic.** `node_type`, `asn`, `isp`, `country_code` are drawn from disjoint pools for licit vs. illicit. | Models using these features learn the generation rule, not real AML patterns. | 🔲 **Needs pool overlap** — some licit txns should use VPNs/Tor, some illicit should use residential/datacenter. |
| 5 | **1-input-1-output only.** Real Bitcoin transactions have multi-input/multi-output UTXOs. No fan-in/fan-out structure exists at the transaction level. | Graph topology is simpler than real Bitcoin. | 🔲 **Acceptable for v1** — document as a simplification. |
| 6 | **`relay_ip` is random, not geo-consistent.** The IP address does not correspond to the stated `country_code`/`asn`. | Cannot validate GeoIP enrichment pipelines against this data. | 🔲 **Acceptable for v1** — use `country_code`/`asn` columns directly. |
| 7 | **`output_wallet` is always unique.** No wallet receives funds from more than one transaction, preventing receive-side graph analysis. | Cannot model wallet clustering by shared receive addresses. | 🔲 **Consider adding wallet reuse on the output side.** |
| 8 | **`txid` range leaks label.** Synthetic heist rows occupy `999000001–999025000`. | Trivial feature extraction risk. | 🔲 **Renumber txids randomly** in next pipeline run. |

---

## 10. Changelog

| Version | Date | Author | Changes | Row Count Δ |
|---------|------|--------|---------|-------------|
| v1.0 | 2026-09-01 | P3 (Data Pipeline) | Initial dataset release. Elliptic labels (46 564 labelled rows → 42 019 licit + 4 545 illicit) + 25 000 appended Bitcoin Heist ransomware rows. Network metadata synthesized via `step5`. | — (baseline: 71 564 rows) |

---

_End of data dictionary._
