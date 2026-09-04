# Simple-Rule Audit — v3

| feature_a           | feature_b          |   depth |    auc |   balanced_acc |
|:--------------------|:-------------------|--------:|-------:|---------------:|
| address_reuse_ratio | edge_to_node_ratio |       2 | 0.932  |         0.9028 |
| edge_to_node_ratio  | max_in_degree      |       2 | 0.926  |         0.914  |
| address_reuse_ratio | edge_to_node_ratio |       1 | 0.9066 |         0.9066 |
| edge_to_node_ratio  | max_in_degree      |       1 | 0.8924 |         0.8924 |
| fanout_ratio        | fanin_ratio        |       2 | 0.8491 |         0.8246 |
| max_chain_length    | max_in_degree      |       2 | 0.8384 |         0.8125 |
| max_chain_length    | max_in_degree      |       1 | 0.8092 |         0.8092 |
| fanout_ratio        | fanin_ratio        |       1 | 0.7554 |         0.7554 |
| time_span_hours     | unique_ip_count    |       2 | 0.7195 |         0.6704 |
| unique_ip_count     | unique_input_addrs |       2 | 0.7041 |         0.6843 |
| num_txns            | unique_ip_count    |       2 | 0.7032 |         0.6642 |
| time_span_hours     | unique_ip_count    |       1 | 0.6604 |         0.6604 |
| unique_ip_count     | unique_input_addrs |       1 | 0.6604 |         0.6604 |
| num_txns            | unique_ip_count    |       1 | 0.6604 |         0.6604 |
| time_span_hours     | num_txns           |       2 | 0.6087 |         0.6038 |
| num_txns            | unique_input_addrs |       2 | 0.5963 |         0.5804 |
| graph_density       | avg_clustering     |       2 | 0.58   |         0.5727 |
| inter_tx_delta_mean | inter_tx_delta_std |       2 | 0.5778 |         0.5604 |
| time_span_hours     | num_txns           |       1 | 0.5769 |         0.5769 |
| graph_density       | avg_clustering     |       1 | 0.5703 |         0.5703 |
| inter_tx_delta_min  | burstiness_B       |       2 | 0.5462 |         0.5448 |
| inter_tx_delta_mean | inter_tx_delta_std |       1 | 0.5439 |         0.5439 |
| inter_tx_delta_min  | burstiness_B       |       1 | 0.5316 |         0.5316 |
| total_input_mean    | total_output_mean  |       2 | 0.5311 |         0.5263 |
| num_txns            | unique_input_addrs |       1 | 0.5291 |         0.5    |
| total_input_mean    | total_output_mean  |       1 | 0.5189 |         0.5189 |

**Best:** `address_reuse_ratio` + `edge_to_node_ratio` depth=2 AUC=0.9320
