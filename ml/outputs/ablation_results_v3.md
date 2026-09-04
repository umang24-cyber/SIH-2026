# Ablation Results — v3


**scale_pos_weight:** 1.0919 (computed from v3 train labels)


| config            |   n_feats |   roc_auc |   pr_auc |     f1 |   precision |   recall |
|:------------------|----------:|----------:|---------:|-------:|------------:|---------:|
| blockchain-only   |        27 |    0.9965 |   0.9964 | 0.9623 |      0.9734 |   0.9515 |
| network-only      |        12 |    0.8904 |   0.8996 | 0.7894 |      0.8029 |   0.7764 |
| combined-no-graph |        39 |    0.9967 |   0.9966 | 0.9639 |      0.9786 |   0.9497 |
| full              |        46 |    0.9967 |   0.9966 | 0.9667 |      0.9787 |   0.9549 |


## Deltas

- Network-only vs blockchain-only: -0.1061
- Combined-no-graph vs blockchain-only: +0.0002
- Full vs blockchain-only: +0.0002
- Graph contribution (full - combined-no-graph): +0.0000

## Interpretation

Network features improve AUC by +0.0002