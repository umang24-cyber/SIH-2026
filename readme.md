# Bitcoin AML Synthetic Dataset (SIH PS 146)

## 1. Dataset Purpose
This repository generates and analyzes a highly realistic, synthetic Bitcoin Anti-Money Laundering (AML) dataset. The purpose is to provide a standardized benchmark for testing graph-based machine learning models against complex, decentralized illicit behaviors on the blockchain.

## 2. V6 Generation
The dataset is currently frozen at **Version 6 (V6)**. V6 resolves historical artifacts (such as Licit dense-graph artificially bounded wallets) by implementing an organic, unbounded wallet pool. It incorporates genuine semantic composites (e.g., ransomware campaigns utilizing mixers for cash-out) to ensure structural overlap between licit and illicit typologies without resorting to arbitrary label swapping.

## 3. Data Flow & Feature Engineering
The exact data flow of the production pipeline is:
1. `generate_v6.py` → Raw `blockchain_transactions.csv` & `network_metadata.csv` (V6 FROZEN)
2. `01_eda_and_validation.py` → Split creation & schema validation
3. `02_feature_engineering.py` → Base structural, temporal, amount, and network features
4. `02b_graph_features.py` → Graph Engine features (Centrality, Assortativity, Clustering)
5. `02c_merge_features.py` → Final Train/Test Feature Matrices
6. `train_production.py` → Model Training & Evaluation

## 4. Scenario-Level Splitting & Leakage Prevention
To prevent data leakage, the entire dataset is split into training and testing sets at the **scenario level** rather than the transaction level. There is strictly zero transaction, address, or scenario overlap between the splits. Labels and generator metadata are systematically stripped before the feature matrices reach the ML pipeline.

## 5. Machine Learning Tasks
The ML architecture is divided into two distinct stages:

### Stage 1: Binary Classification
- **Goal:** Classify scenarios as Licit (0) or Illicit (1).
- **Model:** XGBoost Classifier.
- **Results:** The V6 feature space requires non-linear fusion of structural and temporal metrics, successfully preventing shallow depth-2 trees from solving the task (BAcc ~0.80), while allowing a full XGBoost model to achieve exceptional performance (AUC ~0.999).

### Stage 2: Typology Classification
- **Goal:** Classify illicit scenarios into one of four distinct typologies: Ransomware, Peeling Chain, Layering, or Mixing.
- **Model:** Multi-class XGBoost Classifier (illicit scenarios only).
- **Results:** Achieves Macro-F1 = 1.000.

## 6. Revised Acceptance Methodology (Gate I)
The original Gate I methodology ("Top-3 Individual Feature Ablation") was systematically deprecated. Individual-feature ablation is insufficient in a highly correlated graph-theoretic feature space (e.g., ablating `max_chain_length` causes the model to seamlessly substitute `edge_to_node_ratio`). 

V6 is instead validated using **Feature-Group Ablation** and **Structural-Fingerprint Analysis**. By deleting entire families of features (e.g., all Graph features), we proved that the perfect typology classification is a mathematical consequence of legitimate AML behavior shaping the graphs, and not a deterministic generator artifact.

## 7. Feature Groups
Features are divided into six semantic families:
- **Amount**: Flow of funds, fees, output distributions
- **Temporal**: Time span, burstiness, transaction delays
- **Structural**: Inputs/outputs, address reuse, fan-in/fan-out
- **Network**: ASN counts, Suspicious IP ratios
- **Script**: Transaction scripting complexities
- **Graph**: Density, centrality, assortativity (via networkx engine)

## 8. Reproducibility
The complete production ML pipeline is 100% deterministic. To execute the final models and rebuild all evaluation metrics from the frozen V6 processed features:
```bash
conda activate ml
bash run_production_pipeline.sh
```
Results, logs, and `MANIFEST_v6.json` will be safely output to `ml/models`, `ml/reports`, and `ml/manifests`.

## 9. Known Limitations
- The synthetic dataset, while structurally overlapping, is ultimately bounded by the logic defined in the V6 generator.
- Performance in the wild (against real-world blockchain data) may degrade as unmodeled typologies and zero-day mixing services emerge.
- The default binary classification threshold is `0.50`, which provides an ECE of ~0.007. Thresholds should be tuned based on operational False Positive constraints.
