# Typology Model Metrics — v3


**CV Macro-F1:** 1.0000 ± 0.0000

**Test Macro-F1:** 1.0000


## Per-Class Results

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| layering | 1.0000 | 1.0000 | 1.0000 | 52 |
| mixing | 1.0000 | 1.0000 | 1.0000 | 64 |
| peeling_chain | 1.0000 | 1.0000 | 1.0000 | 52 |
| ransomware | 1.0000 | 1.0000 | 1.0000 | 409 |

## Confusion Matrix

|               |   pred_layering |   pred_mixing |   pred_peeling_chain |   pred_ransomware |
|:--------------|----------------:|--------------:|---------------------:|------------------:|
| layering      |              52 |             0 |                    0 |                 0 |
| mixing        |               0 |            64 |                    0 |                 0 |
| peeling_chain |               0 |             0 |                   52 |                 0 |
| ransomware    |               0 |             0 |                    0 |               409 |