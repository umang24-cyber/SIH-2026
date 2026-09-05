# Single-Feature AUC Audit — v3

| feature                |    auc |   best_threshold | direction       |   balanced_acc |   precision |   recall |
|:-----------------------|-------:|-----------------:|:----------------|---------------:|------------:|---------:|
| edge_to_node_ratio     | 0.9067 |           0.8519 | higher->illicit |         0.8916 |      0.9148 |   0.8562 |
| address_reuse_ratio    | 0.9056 |           0.0222 | higher->illicit |         0.897  |      0.9978 |   0.7955 |
| max_in_degree          | 0.8044 |           2      | higher->illicit |         0.8092 |      0.9734 |   0.6343 |
| fanout_ratio           | 0.7353 |          -1.3333 | lower->illicit  |         0.7554 |      0.84   |   0.6187 |
| suspicious_infra_ratio | 0.7316 |           0.4    | higher->illicit |         0.7384 |      0.6937 |   0.8007 |
| unique_asn_count       | 0.6691 |           3      | higher->illicit |         0.6889 |      1      |   0.3778 |
| mean_num_outputs       | 0.6587 |          -1.6364 | lower->illicit  |         0.6861 |      0.7101 |   0.5945 |
| unique_country_count   | 0.6465 |           3      | higher->illicit |         0.6525 |      1      |   0.305  |
| io_count_ratio         | 0.6458 |           0.7074 | higher->illicit |         0.6392 |      0.6161 |   0.6482 |
| unique_ip_count        | 0.6439 |           3      | higher->illicit |         0.6604 |      0.7108 |   0.5113 |
| asn_concentration      | 0.6398 |          -0.5    | lower->illicit  |         0.6346 |      0.8304 |   0.331  |
| country_concentration  | 0.6205 |          -0.5    | lower->illicit  |         0.6127 |      0.8159 |   0.2842 |
| fanin_ratio            | 0.6124 |          -0.9675 | lower->illicit  |         0.6276 |      0.7439 |   0.3726 |
| output_amount_gini     | 0.6069 |          -0.6285 | lower->illicit  |         0.5859 |      0.5459 |   0.721  |
| max_chain_length       | 0.605  |           5      | higher->illicit |         0.5898 |      0.6348 |   0.3795 |
| graph_density          | 0.593  |           0.0283 | higher->illicit |         0.6021 |      0.5574 |   0.7487 |
| mean_num_inputs        | 0.5912 |          -1.125  | lower->illicit  |         0.6548 |      0.6272 |   0.6794 |
| amount_decay_slope     | 0.5727 |           0.0036 | lower->illicit  |         0.5745 |      0.5609 |   0.5269 |
| unique_output_addrs    | 0.5637 |         -36      | lower->illicit  |         0.5621 |      0.5131 |   0.948  |
| denomination_entropy   | 0.5533 |          -1.5    | lower->illicit  |         0.5516 |      0.6268 |   0.227  |
| unique_user_agents     | 0.5481 |           3      | higher->illicit |         0.5501 |      0.5203 |   0.6447 |
| unique_input_addrs     | 0.5474 |           9      | higher->illicit |         0.5543 |      0.5345 |   0.5373 |
| num_txns               | 0.5436 |           5      | higher->illicit |         0.5597 |      0.5246 |   0.7019 |
| time_span_hours        | 0.5402 |           2.0804 | higher->illicit |         0.5775 |      0.5288 |   0.8423 |
| hour_of_day_entropy    | 0.5394 |           1      | higher->illicit |         0.5532 |      0.5107 |   0.8683 |
| burstiness_B           | 0.5391 |           0.0106 | higher->illicit |         0.5513 |      0.6171 |   0.2374 |
| degree_assortativity   | 0.5385 |           0.2091 | lower->illicit  |         0.5662 |      0.5411 |   0.5927 |
| inter_tx_delta_mean    | 0.5367 |        2961      | higher->illicit |         0.5553 |      0.5141 |   0.8232 |
| script_type_entropy    | 0.5366 |           0.971  | higher->illicit |         0.5363 |      0.5035 |   0.7504 |
| prop_delta_std         | 0.5322 |          63.3616 | higher->illicit |         0.534  |      0.4985 |   0.8648 |
| inter_tx_delta_std     | 0.5322 |        1496.1    | higher->illicit |         0.5517 |      0.5147 |   0.7574 |
| inter_tx_delta_min     | 0.5302 |          16      | higher->illicit |         0.5254 |      0.4925 |   0.9047 |
| fee_ratio_mean         | 0.5294 |          -0.001  | lower->illicit  |         0.5488 |      0.5874 |   0.2738 |
| io_amount_similarity   | 0.5294 |           0.999  | higher->illicit |         0.5488 |      0.5874 |   0.2738 |
| prop_delta_mean        | 0.5286 |         257.25   | higher->illicit |         0.529  |      0.5    |   0.6898 |
| round_number_ratio     | 0.5286 |          -0      | lower->illicit  |         0.5334 |      0.4995 |   0.8128 |
| ip_to_addr_ratio       | 0.5223 |           0.0833 | higher->illicit |         0.5331 |      0.496  |   0.9567 |
| script_type_mode       | 0.5201 |          -0      | lower->illicit  |         0.5179 |      0.4907 |   0.7279 |
| total_input_mean       | 0.5189 |           1.7971 | higher->illicit |         0.5324 |      0.7571 |   0.0919 |
| total_output_mean      | 0.5189 |           1.7969 | higher->illicit |         0.5324 |      0.7571 |   0.0919 |
| prop_delta_cv          | 0.5164 |           0.2204 | higher->illicit |         0.5301 |      0.496  |   0.8666 |
| fee_ratio_std          | 0.5123 |          -0.0009 | lower->illicit  |         0.5348 |      0.5396 |   0.3189 |
| alt_port_ratio         | 0.512  |           0.1429 | higher->illicit |         0.5273 |      0.5096 |   0.461  |
| change_output_ratio    | 0.508  |           0.0714 | higher->illicit |         0.5247 |      0.4937 |   0.8128 |
| max_out_degree         | 0.5035 |           5      | higher->illicit |         0.5772 |      0.8175 |   0.1941 |
| avg_clustering         | 0.5    |           0      | higher->illicit |         0.5    |      0.478  |   1      |

**Best:** `edge_to_node_ratio` AUC=0.9067
