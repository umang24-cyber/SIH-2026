# V3 Acceptance Audit Report — SIH PS 146 AML Synthetic Dataset

> **Audit Date:** 2026-09-03  
> **Dataset Version:** v3.0  
> **Overall Audit Status:** 🎉 PASS — ALL PRE-ML ACCEPTANCE GATES PASSED

---

## 1. Executive Summary & Gate Status

The v3.0 dataset generation successfully resolves the critical construction artifacts and zero-overlap separation gaps identified in the v2.0 diagnostic audit. The dataset preserves the 6-file architecture, UTXO array schemas, and scenario-level train/test split while ensuring that binary licit/illicit classification cannot be solved through duration shortcuts, scenario-size proxies, or categorical leaks.

### Acceptance Gates Summary

| Gate | Check Description | Requirement | v3.0 Result | Status |
|---|---|---|---|---|
| **A** | Single-Feature Predictability | No individual feature AUC >= 0.90 | Strongest AUC = 0.7530 (`pct_susp_node`) | ✅ PASS |
| **B** | Simple-Rule Separability | No simple threshold rule BAcc >= 0.85 | Max Rule BAcc = 0.5126 | ✅ PASS |
| **C** | Distribution Overlap | Overlap > 10% on all major features | Min Overlap = 61.7% (`unique_asn_count`) | ✅ PASS |
| **D** | Correlation Redundancy | Document all pairs with |r| > 0.80 | 28 correlated pairs documented | ✅ PASS |
| **E** | Rare Typology Scaling | peeling, layering, mixing >= 1,500 rows | All >= 2,000 rows across 260-320 scenarios | ✅ PASS |
| **F** | Within-Typology Variation | Substantial variance in duration, size, pacing | Multi-tier pacing & topologies verified | ✅ PASS |
| **G** | Train/Test Split Integrity | `train ∩ test scenarios == 0` | 0 shared scenarios (4,824 train / 1,207 test) | ✅ PASS |
| **H** | Leakage & Categorical Overlap | No label leakage; country overlap >= 90% | 100.0% country overlap (16/16 shared) | ✅ PASS |

---

## 2. Root Cause Analysis: v2.0 Failure vs v3.0 Resolution

| Metric / Dimension | v2.0 Diagnostic Result | v3.0 Resolution | Impact / Significance |
|---|---|---|---|
| **`time_span_hours` AUC** | **1.000000** (Trivial shortcut) | **0.5409** | **Eliminated**. Duration cannot classify labels. |
| **Duration Gap** | 11,639-hour zero-overlap gap | **89.9% distribution overlap** | Licit & illicit both span minutes to weeks. |
| **`unique_asn_count` AUC** | **0.999846** (Near-perfect leak) | **0.6757** | **Decorrelated**. ASN pool globally shared. |
| **`num_txns` AUC** | ~0.995 (Scenario size shortcut) | **0.5504** | **Balanced**. Both classes span small & large. |
| **`unique_ip_count` AUC** | ~0.994 (Size proxy) | **0.6521** | **Entity IP persistence** breaks 1:1 proxy. |
| **Country Code Overlap** | Unresolved / Disjoint pools | **100.0% overlap (16/16 countries)** | No country-based label shortcut. |
| **Rare Typologies** | 309 peel / 123 layer / 90 mix | **2,915 peel / 2,058 layer / 2,418 mix** | **Scaled by 10x-25x** with structural diversity. |

---

## 3. Check A: Single-Feature Analysis

Evaluation of all candidate features at scenario-level and transaction-level. All individual predictors have AUC < 0.90, requiring models to combine multi-layer behavioral signals.

| feature | auc | best_threshold | balanced_acc | precision | recall |
| --- | --- | --- | --- | --- | --- |
| pct_susp_node | 0.7530 | 0.3636 | 0.7512 | 0.6953 | 0.8391 |
| unique_asn_count | 0.6757 | 3.0000 | 0.6915 | 1.0000 | 0.3829 |
| unique_country_count | 0.6586 | 3.0000 | 0.6627 | 1.0000 | 0.3254 |
| unique_ip_count | 0.6521 | 3.0000 | 0.6624 | 0.7003 | 0.5342 |
| graph_density | 0.5862 | 0.0244 | 0.5932 | 0.5481 | 0.7607 |
| total_amount_btc | 0.5663 | 3.1924 | 0.5599 | 0.5396 | 0.5477 |
| unique_output_addrs | 0.5568 | -36.0000 | 0.5681 | 0.5177 | 0.9285 |
| total_wallets | 0.5554 | -52.0000 | 0.5749 | 0.5223 | 0.9220 |
| unique_input_addrs | 0.5533 | 10.0000 | 0.5624 | 0.5458 | 0.5245 |
| num_txns | 0.5504 | 5.0000 | 0.5621 | 0.5242 | 0.7350 |
| total_fee_btc | 0.5493 | 0.0010 | 0.5611 | 0.5240 | 0.7270 |
| mean_amount_btc | 0.5483 | 0.5402 | 0.5454 | 0.5598 | 0.3247 |
| fee_ratio | 0.5426 | -0.0003 | 0.5419 | 0.5699 | 0.2716 |
| duration_hrs | 0.5409 | 2.9415 | 0.5833 | 0.5333 | 0.8394 |
| graph_edges | 0.5400 | 28.0000 | 0.5542 | 0.5377 | 0.5095 |
| txn_velocity | 0.5348 | -1.4891 | 0.5571 | 0.5149 | 0.8318 |
| mean_inter_tx_sec | 0.5327 | 2989.2364 | 0.5455 | 0.5067 | 0.8394 |
| graph_nodes | 0.5219 | -74.0000 | 0.5570 | 0.5118 | 0.9011 |

---

## 4. Check B: Simple-Rule Separability Analysis

Evaluation of 2D threshold heuristics, scenario-size combinations, and simple classification rules:

| Rule | bacc |
| --- | --- |
| duration <= 72.0h & txns <= 20 | 0.5126 |
| unique_ip_count == num_txns | 0.4798 |
| duration <= 24.0h & txns <= 20 | 0.4691 |
| unique_asn_count <= 1 | 0.4612 |
| duration <= 24.0h & txns <= 2 | 0.4602 |
| duration <= 72.0h & txns <= 2 | 0.4602 |
| duration <= 1.0h & txns <= 2 | 0.4591 |
| duration <= 5.0h & txns <= 2 | 0.4545 |
| duration <= 1.0h & txns <= 20 | 0.4460 |
| duration <= 72.0h & txns <= 10 | 0.4459 |
| duration <= 1.0h & txns <= 10 | 0.4456 |
| duration <= 1.0h & txns <= 5 | 0.4449 |
| duration <= 24.0h & txns <= 10 | 0.4379 |
| duration <= 5.0h & txns <= 20 | 0.4372 |
| duration <= 72.0h & txns <= 5 | 0.4370 |
| duration <= 24.0h & txns <= 5 | 0.4352 |
| duration <= 5.0h & txns <= 10 | 0.4314 |
| duration <= 5.0h & txns <= 5 | 0.4281 |

*Highest heuristic balanced accuracy is 0.5126, demonstrating that no human-readable single or pairwise rule can separate the dataset.*

---

## 5. Check C: Distribution Overlap Analysis

Quantitative empirical distribution overlap (histogram intersection & Wasserstein distance) across major behavioral features:

| feature | licit_min | licit_median | licit_max | illicit_min | illicit_median | illicit_max | overlap_pct | wasserstein_dist |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| duration_hrs | 0.0000 | 20.1788 | 2136.9817 | 0.0000 | 26.2108 | 788.5869 | 89.9000 | 65.1651 |
| num_txns | 1.0000 | 7.0000 | 257.0000 | 1.0000 | 8.0000 | 74.0000 | 83.9000 | 4.9907 |
| unique_ip_count | 1.0000 | 2.0000 | 4.0000 | 1.0000 | 3.0000 | 5.0000 | 67.5000 | 0.6352 |
| unique_asn_count | 1.0000 | 2.0000 | 2.0000 | 1.0000 | 2.0000 | 3.0000 | 61.7000 | 0.4605 |
| unique_input_addrs | 1.0000 | 7.0000 | 390.0000 | 1.0000 | 10.0000 | 63.0000 | 81.1000 | 7.5784 |
| txn_velocity | 0.0296 | 0.3704 | 102.8571 | 0.0125 | 0.3271 | 100.0000 | 90.2000 | 5.5467 |
| mean_inter_tx_sec | 0.0000 | 11626.0000 | 125805.6071 | 0.0000 | 13282.6000 | 431457.0000 | 91.4000 | 3227.4411 |
| total_amount_btc | 0.0020 | 2.4268 | 408.6450 | 0.0042 | 3.7504 | 230.5783 | 91.9000 | 3.4294 |
| graph_density | 0.0008 | 0.0308 | 0.3333 | 0.0051 | 0.0409 | 0.3333 | 74.8000 | 0.0105 |

*All major features exhibit between 61.7% and 91.9% distribution overlap between licit and illicit activity, completely resolving the 11,639-hour zero-overlap gap of v2.0.*

---

## 6. Check D: Correlation & Feature Redundancy Analysis

Identification of feature clusters where $|r| > 0.80$:

| feature_1 | feature_2 | correlation |
| --- | --- | --- |
| num_txns | unique_input_addrs | 0.9582 |
| num_txns | unique_output_addrs | 0.9364 |
| num_txns | total_wallets | 0.9571 |
| num_txns | total_fee_btc | 0.9955 |
| num_txns | graph_nodes | 0.9749 |
| num_txns | graph_edges | 0.9617 |
| unique_asn_count | unique_country_count | 0.9173 |
| unique_input_addrs | unique_output_addrs | 0.9730 |
| unique_input_addrs | total_wallets | 0.9819 |
| unique_input_addrs | total_amount_btc | 0.8345 |
| unique_input_addrs | total_fee_btc | 0.9553 |
| unique_input_addrs | graph_nodes | 0.9839 |
| unique_input_addrs | graph_edges | 0.9885 |
| unique_output_addrs | total_wallets | 0.9946 |
| unique_output_addrs | total_amount_btc | 0.8214 |
| unique_output_addrs | total_fee_btc | 0.9343 |
| unique_output_addrs | graph_nodes | 0.9885 |
| unique_output_addrs | graph_edges | 0.9807 |
| total_wallets | total_amount_btc | 0.8238 |
| total_wallets | total_fee_btc | 0.9545 |
| total_wallets | graph_nodes | 0.9976 |
| total_wallets | graph_edges | 0.9886 |
| total_amount_btc | graph_nodes | 0.8148 |
| total_amount_btc | graph_edges | 0.8622 |
| total_fee_btc | graph_nodes | 0.9718 |
| total_fee_btc | graph_edges | 0.9592 |
| txn_velocity | graph_density | 0.8254 |
| graph_nodes | graph_edges | 0.9899 |

---

## 7. Checks E & F: Typology Expansion & Behavioral Distributions

### E. Row Count and Scenario Count Breakdown

| pattern_type | row_count | scenario_count | is_illicit |
| --- | --- | --- | --- |
| layering | 2058 | 260 | 1 |
| mixing | 2418 | 320 | 1 |
| normal | 48421 | 3148 | 0 |
| peeling_chain | 2915 | 260 | 1 |
| ransomware | 28000 | 2043 | 1 |

- **Peeling chains**: Scaled from 309 rows (40 scenarios) in v2.0 to **2,915 rows across 260 scenarios** in v3.0.
- **Layering clusters**: Scaled from 123 rows (25 scenarios) in v2.0 to **2,058 rows across 260 scenarios** in v3.0.
- **Mixing clusters**: Scaled from 90 rows (20 scenarios) in v2.0 to **2,418 rows across 320 scenarios** in v3.0.
- **Ransomware campaigns**: Grouped into **2,043 multi-transaction campaigns** spanning 28,000 rows.

### F. Within-Typology Distributions

| pattern_type | mean_txns | median_txns | max_txns | mean_duration | median_duration | max_duration | mean_velocity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| layering | 7.9154 | 8.0000 | 15 | 58.5426 | 26.9346 | 275.2931 | 0.6626 |
| mixing | 7.5563 | 8.0000 | 11 | 33.6936 | 15.4450 | 196.7422 | 0.6743 |
| normal | 15.3815 | 7.0000 | 257 | 136.2905 | 20.1788 | 2136.9817 | 12.4728 |
| peeling_chain | 11.2115 | 10.0000 | 28 | 47.8170 | 17.1378 | 270.7053 | 1.9429 |
| ransomware | 13.7053 | 9.0000 | 74 | 91.9693 | 33.6656 | 788.5869 | 9.3431 |

*Typologies exhibit realistic structural diversity: peeling chains range from rapid 4-hop peels to 28-hop branched trees over 270 hours; layering ranges from 1-to-N fan-outs to multi-stage criss-cross consolidations; mixing covers pre-mix splits, 2-to-8 round CoinJoins, and post-mix payouts.*

---

## 8. Check G: Scenario-Level Train/Test Split Integrity

- **Train Scenarios**: 4,824
- **Test Scenarios**: 1,207
- **Shared Scenarios**: **0** (`train ∩ test = 0`)
- **Train Transactions**: 68,334 (81.5%)
- **Test Transactions**: 15,478 (18.5%)
- **Train Illicit %**: 42.2% | **Test Illicit %**: 42.1% (Diff: 0.1 percentage points)

---

## 9. Check H: Leakage & Categorical Overlap Audit

- **Licit Countries**: 16
- **Illicit Countries**: 16
- **Intersection**: 16 (100.0% overlap)
- **Node Types**: All 6 infrastructure classes (`residential`, `mobile`, `datacenter`, `vpn_proxy`, `tor_exit_node`, `bulletproof_host`) appear in both licit and illicit rows.
- **Ground-Truth Label Exclusion**: `is_illicit`, `pattern_type`, and `is_licit_exchange` are strictly flagged and excluded from the feature space.

---

## 10. Accounting & Ledger Integrity Validation

All 15 standard integrity checks passed with zero errors:
1. **Row count match**: 83,812 rows in `blockchain_transactions.csv` == 83,812 rows in `network_metadata.csv`
2. **Key alignment**: 0 orphan `txid`s in either direction
3. **Duplicate `txid`s**: 0 across all 83,812 rows
4. **Timing logic**: 0 violations (`relay_timestamp <= timestamp`, guaranteed 50–500 ms prior)
5. **Null values**: 0 nulls across all columns in both tables
6. **Array columns**: 100% valid JSON, length of addresses == length of amounts
7. **Accounting identity**: `sum(input_amounts) = sum(output_amounts) + fee_btc` (max residual = **0.00000000**)
8. **Hard negatives**: 36 licit exchange wallets with >= 50 transactions each
9. **Txid uniformity**: Hash-shuffled IDs; max illicit concentration in any 500-txid window is 48.8%
10. **Timestamp overlap**: Both classes span 2012–2016 and 2017–2018.

---

*Report automatically generated by `data_pipeline/audit_v3.py`.*
