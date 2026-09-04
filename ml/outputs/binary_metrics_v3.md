# Binary Model Metrics — v3

## Dataset
- Train scenarios: 4,824 | Test scenarios: 1,207
- Licit: 52.2% (2,518) | Illicit: 47.8% (2,306)
- scale_pos_weight: 1.0919 (computed dynamically)

## Test Set Performance
| Metric | Value |
|---|---|
| ROC-AUC | 0.9965 |
| PR-AUC | 0.9964 |
| F1 (macro) | 0.9650 |
| F1 (licit) | 0.9700 |
| F1 (illicit) | 0.9600 |
| Precision (licit) | 0.9400 |
| Recall (licit) | 1.0000 |
| Precision (illicit) | 1.0000 |
| Recall (illicit) | 0.9300 |
| Accuracy | 0.9600 |

## Calibration
- Method: Isotonic regression
- ECE (raw): 0.0151 | ECE (calibrated): 0.0073
- Brier score: 0.0229

## Top-10 Features (gain-based importance)
| Rank | Feature | Share |
|---|---|---|
| 1 | address_reuse_ratio | 42.0% |
| 2 | max_in_degree | 11.0% |
| 3 | edge_to_node_ratio | 4.9% |
| 4 | ip_to_addr_ratio | 4.5% |
| 5 | unique_input_addrs | 3.8% |
| 6 | unique_output_addrs | 3.2% |
| 7 | fanout_ratio | 2.6% |
| 8 | fanin_ratio | 2.5% |
| 9 | num_txns | 2.5% |
| 10 | graph_density | 2.5% |

## Shortcut Audit
- Best single-feature AUC: edge_to_node_ratio = 0.9067
- Best pairwise rule AUC: address_reuse_ratio + edge_to_node_ratio (depth-2) = 0.9320
- Full model vs best pairwise rule: +0.0645 AUC improvement
- Near-perfect shortcut (>=0.97): NONE

## Interpretation
The model substantially outperforms the best simple rule (0.9965 vs 0.9320). 
address_reuse_ratio (42% gain share) is a genuine forensic signal — illicit 
scenarios structurally require address reuse (peeling chains reuse change outputs, 
layering reuses consolidation addresses, mixing uses pre/post-mix aggregation).
Normal licit scenarios (exchange wallets) consistently use fresh addresses per 
transaction by design.
