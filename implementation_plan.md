# P5 ML Execution Plan — SIH PS 146: Bitcoin AML

> **Scope**: Feature extraction → model training → explainability.
> **Timeline**: Days 3–8 of hackathon (~5-6 focused working days).
> **Conda env**: `ml` (has sklearn 1.9, scipy, matplotlib, seaborn; needs xgboost, shap, networkx).

---

## Verified Dataset Reality (from actual data exploration)

| Pattern | Train Scenarios | Test Scenarios | Txns/Scenario (median) |
|---------|:-:|:-:|:-:|
| ransomware | 12,897 | 3,225 | 2 |
| normal | 1,125 | 281 | 32 |
| peeling_chain | 32 | 8 | 8 |
| layering | 20 | 5 | 5 |
| mixing | 16 | 4 | 4 |
| **Total** | **14,090** | **3,523** | — |

> [!CAUTION]
> **Class scarcity is severe.** Layering has 5 test scenarios, mixing has 4. A 5-class multiclass model evaluated on the fixed test split is statistically meaningless for these classes — a single misclassification moves accuracy by 20-25%. This fundamentally shapes the plan.

> [!IMPORTANT]
> **Label homogeneity verified**: 0 scenarios have mixed `is_illicit` or `pattern_type` within them. Scenario-level aggregation is safe.

---

## Hard Dependencies on Teammates

| Dependency | Who | What I need | Fallback if unavailable by Day 3 EOD |
|---|---|---|---|
| **Graph object or API** | P4 (Graph) | Pre-computed per-scenario topological features (hop count, reconvergence count, subgraph density, clustering coefficient, external-degree ratio) from the Neo4j/NetworkX graph | **Fallback**: Build a lightweight `networkx` wallet→tx bipartite graph myself from the array columns. I can compute degree, fan-out/fan-in, and chain-length. I *cannot* compute true reconvergence or community-level density without the full graph — those features get stubbed as NaN and the model trains without them. |
| **Scenario metadata** | P3 (Data) | Confirmation that `scenario_id` is the only grouping key needed; no scenario hierarchy exists | Already confirmed via data dictionary v2.0. No action needed. |
| **Dashboard inference API** | P1/P2 (Dashboard) | Expected input/output JSON schema for the model inference endpoint | **Fallback**: I define the schema myself (input: scenario features dict → output: `{is_illicit, confidence, typology, typology_confidence, explanation_text}`) and hand it off on Day 5. |

> [!IMPORTANT]
> **Day 1 action item**: Message P4 with this exact question: *"Will you provide me a function/file I can call like `get_scenario_features(scenario_id) -> dict` with topological features, or should I build my own graph from the raw CSVs? I need an answer by end of Day 3 to unblock feature engineering."*

---

## Corrections & Extensions to Your Feature-Group List

Your feature groups are directionally correct. Here are concrete corrections and additions:

### ✅ What's correct
- Graph-topological group: solid list, reconvergence count is the key layering signal.
- Temporal: inter-hop delta stats and burstiness are good.
- Amount-based: decay ratio and round-number flags are correct.
- Network-layer: Tor/VPN ratio and ASN diversity are appropriate.

### ⚠️ Corrections

1. **"Hop count" is ambiguous** — for peeling chains it's the chain length (longest path in the scenario subgraph), for fan-out/fan-in it's the diameter of the bipartite subgraph. Define these as *two separate features*: `chain_length_max` (longest directed path) and `subgraph_diameter`.

2. **"Subgraph density" alone is misleading** — a 3-tx peeling chain and a 3-tx mixing round have very different densities despite similar tx counts. You need density *normalized by expected density for that topology*, which is circular. Instead, use **edge-to-node ratio** and **clustering coefficient** separately — they're more interpretable and less correlated.

3. **"Burstiness" is underspecified** — use the **burstiness parameter** `B = (σ_τ - μ_τ) / (σ_τ + μ_τ)` where τ is inter-event time. Ranges from -1 (periodic) to +1 (bursty). Mixing is periodic (B ≈ -0.5 to 0), peeling is bursty (B ≈ 0.5-0.8).

4. **"Round-number flags" is too simplistic** — use **denomination entropy**: `H = -Σ p_i log(p_i)` over binned output amounts. Mixing has very low entropy (few distinct output sizes), normal has high entropy.

### ➕ Missing features you should add

| Feature | Why | Typology signal |
|---|---|---|
| `change_output_ratio` | Fraction of outputs that are "change" (amount close to largest input minus one output) | Peeling chains ≈ 0.5 (1 payment + 1 change per hop) |
| `address_reuse_ratio` | Fraction of output addresses that reappear as inputs in other txns within the same scenario | Peeling chains ≈ high (change address is next hop's input) |
| `io_count_ratio` | `mean(num_inputs) / mean(num_outputs)` across scenario txns | Mixing ≈ 1.0 (N-in, N-out), layering fan-out ≈ 0.1-0.3 |
| `amount_concentration_gini` | Gini coefficient of output amounts across the scenario | Mixing ≈ 0 (equal outputs), normal ≈ high |
| `fee_ratio_std` | Std of `fee_btc / total_input` across txns in scenario | Peeling chains have very consistent fee ratios |
| `script_type_entropy` | Entropy of script_type distribution within scenario | Mixing tends to use uniform script types |
| `propagation_delta_cv` | Coefficient of variation of `timestamp - relay_timestamp` across scenario | Operational consistency signal |
| `unique_country_count` | Count of distinct `country_code` values in the scenario | Geographic dispersion of relays |
| `suspicious_infra_ratio` | Fraction of txns relayed via `tor_exit_node`, `vpn_proxy`, or `bulletproof_host` | Key network-layer signal (but deliberately noisy in v2.0) |

---

## Model Architecture Decision: Binary + Hierarchical, Not Flat 5-Class

> [!IMPORTANT]
> **Critical design decision** — requesting your sign-off.

Given the class distribution, I recommend a **two-stage approach**, not a single flat 5-class model:

### Stage 1: Binary classifier (is_illicit)
- **14,090 train / 3,523 test scenarios** — statistically robust evaluation.
- XGBoost with `scale_pos_weight` (class ratio ≈ 1.04, nearly balanced at scenario level — verify after aggregation).
- This is the **primary deliverable** and the one judges can meaningfully evaluate.

### Stage 2: Typology classifier (pattern_type), illicit scenarios only
- Train only on the **illicit subset** (12,949 train scenarios: 12,897 ransomware + 32 peeling + 20 layering + 16 mixing → extremely imbalanced).
- **Fixed test split is NOT usable** for peeling/layering/mixing evaluation (8/5/4 test scenarios). Instead:
  - Use **leave-one-scenario-out cross-validation (LOSOCV)** across all 68 rare-typology scenarios (32+20+16) to get per-fold predictions and aggregate metrics.
  - Report LOSOCV macro-F1 for the rare typologies in the demo.
  - For the ransomware-vs-rest distinction, the fixed split is fine.
- **Practical framing for judges**: "The binary detector (Stage 1) has full statistical power. The typology classifier (Stage 2) successfully distinguishes structural patterns but is trained on limited scenarios — we report LOSOCV results to be honest about this."

### Why not flat 5-class?
- `normal` scenarios (1,125 train) are NOT in the same decision space as `ransomware` (12,897 train). A flat 5-class model would spend 99% of its capacity on the ransomware-vs-normal boundary, which is the same as the binary model.
- The interesting question — "what *kind* of illicit is this?" — only matters for the illicit subset, and the class balance within that subset is wildly skewed (12,897 : 32 : 20 : 16).

---

## Day-by-Day Execution Plan

---

### Day 1 (Sep 2-3): Environment Setup + EDA + Scenario Aggregation

#### Tasks
1. **Environment setup** (~30 min)
   ```bash
   conda activate ml
   conda install -c conda-forge xgboost shap networkx -y
   ```
   Create project structure:
   ```
   ml/
   ├── 01_eda_and_validation.py
   ├── 02_feature_engineering.py
   ├── 03_train_binary.py
   ├── 04_train_typology.py
   ├── 05_explainability.py
   ├── 06_ablation.py
   ├── inference.py          # final inference entry point
   ├── models/               # saved model artifacts
   └── outputs/              # plots, reports, SHAP htmls
   ```

2. **EDA & validation notebook** (`01_eda_and_validation.py`) (~2 hrs)
   - ✅ Already confirmed: label homogeneity within scenarios (0 violations).
   - Compute and visualize scenario-level class distribution (bar charts by pattern_type).
   - Verify the 30 hard-negative exchange scenarios: confirm they're high-txn-count, licit, fan-out/fan-in shaped.
   - Plot scenario size distributions per pattern_type (box plots).
   - Parse all JSON array columns, validate lengths match between addresses and amounts.
   - Compute and print the *scenario-level* class balance for binary and multiclass.
   - **Output**: `outputs/eda_report.md` with key stats and plots.

3. **Scenario aggregation script** (`02_feature_engineering.py` — Phase 1) (~3 hrs)
   - Join `blockchain_transactions.csv` + `network_metadata.csv` on `txid`.
   - `groupby('scenario_id')` and compute all features (see feature table below).
   - Output: `data/processed/scenario_features_train.csv` and `scenario_features_test.csv`.
   - Each row = one scenario, columns = features + `scenario_id` + `is_illicit` + `pattern_type` (labels held separately, not in feature matrix).

#### Feature Computation Table (Phase 1 — no graph dependency)

**Amount features** (from array columns):
| Feature | Computation |
|---|---|
| `total_input_mean` | `mean(sum(input_amounts))` across scenario txns |
| `total_output_mean` | `mean(sum(output_amounts))` across scenario txns |
| `fee_ratio_mean` | `mean(fee_btc / sum(input_amounts))` |
| `fee_ratio_std` | `std(fee_btc / sum(input_amounts))` |
| `amount_decay_slope` | Linear regression slope of `sum(output_amounts)` over txn order (time-sorted) |
| `output_amount_gini` | Gini coefficient over all output amounts in scenario |
| `denomination_entropy` | Entropy of binned output amounts |
| `round_number_ratio` | Fraction of outputs that are round numbers (within 1% of 0.01, 0.1, 0.5, 1.0, etc.) |
| `io_amount_similarity` | `1 - abs(sum_inputs - sum_outputs) / sum_inputs` averaged across txns (≈ 1.0 minus fee ratio) |

**Structural features** (from array columns, no graph needed):
| Feature | Computation |
|---|---|
| `num_txns` | Count of txns in scenario |
| `mean_num_inputs` | `mean(len(input_addresses))` |
| `mean_num_outputs` | `mean(len(output_addresses))` |
| `io_count_ratio` | `mean_num_inputs / mean_num_outputs` |
| `unique_input_addrs` | Count of distinct input addresses |
| `unique_output_addrs` | Count of distinct output addresses |
| `address_reuse_ratio` | `|input_addrs ∩ output_addrs| / |output_addrs|` within scenario |
| `change_output_ratio` | Heuristic: fraction of outputs where `amount ≈ largest_input - other_output` |
| `fanout_ratio` | `unique_output_addrs / num_txns` |
| `fanin_ratio` | `unique_input_addrs / num_txns` |
| `script_type_entropy` | Entropy of script_type distribution |
| `script_type_mode` | Most common script_type (label-encoded) |

**Temporal features**:
| Feature | Computation |
|---|---|
| `time_span_hours` | `(max(timestamp) - min(timestamp)).total_seconds() / 3600` |
| `inter_tx_delta_mean` | Mean seconds between consecutive txns (time-sorted) |
| `inter_tx_delta_std` | Std of inter-txn deltas |
| `inter_tx_delta_min` | Min inter-txn delta |
| `burstiness_B` | `(σ - μ) / (σ + μ)` of inter-txn deltas |
| `hour_of_day_entropy` | Entropy of hour-of-day distribution |
| `prop_delta_mean` | Mean of `(timestamp - relay_timestamp)` in ms |
| `prop_delta_std` | Std of propagation deltas |
| `prop_delta_cv` | `prop_delta_std / prop_delta_mean` |

**Network-layer features**:
| Feature | Computation |
|---|---|
| `suspicious_infra_ratio` | Fraction of txns with `node_type ∈ {tor_exit_node, vpn_proxy, bulletproof_host}` |
| `unique_asn_count` | Distinct ASNs in scenario |
| `asn_concentration` | Max frequency of any single ASN / num_txns |
| `unique_country_count` | Distinct country codes |
| `country_concentration` | Max frequency of any single country / num_txns |
| `unique_ip_count` | Distinct relay IPs |
| `ip_to_addr_ratio` | `unique_ip_count / unique_input_addrs` |
| `alt_port_ratio` | Fraction of txns using non-8333 ports |
| `unique_user_agents` | Distinct user_agent strings |

#### Validation Checks (Gate for Day 2)
- [ ] `scenario_features_train.csv` has exactly 14,090 rows.
- [ ] `scenario_features_test.csv` has exactly 3,523 rows.
- [ ] Zero NaN in any feature column (except graph-dependent features if P4 hasn't delivered).
- [ ] `is_illicit` and `pattern_type` are NOT in the feature columns.
- [ ] Correlation matrix: no feature has >0.95 Pearson correlation with `is_illicit` (would indicate label leakage).
- [ ] The 30 hard-negative exchange scenarios have high `num_txns`, high `fanout_ratio`, and `is_illicit = 0`.

#### P4 Dependency Action
> **Send to P4 today**: "I need either (a) a `scenario_graph_features.csv` with columns `[scenario_id, hop_count, reconvergence_count, subgraph_density, clustering_coeff, external_degree_ratio]`, or (b) a function I can call to get these. Need it by end of Day 3. If you can't deliver, I'll build a lightweight version from the array columns."

---

### Day 2 (Sep 3-4): Graph Features (Fallback) + Binary Model v1

#### Tasks
1. **Graph feature fallback** (~2 hrs, skip if P4 delivers)
   - Build a per-scenario `networkx.DiGraph` from the array columns:
     - For each txn: add edges `input_addr → txid` and `txid → output_addr` with amount weights.
   - Compute:
     | Feature | Method |
     |---|---|
     | `max_chain_length` | Longest simple path in the scenario subgraph (DAG — use `nx.dag_longest_path_length` if acyclic, else BFS with depth limit=15) |
     | `graph_density` | `nx.density()` |
     | `avg_clustering` | `nx.average_clustering()` on undirected projection |
     | `max_in_degree` | Max in-degree of any address node |
     | `max_out_degree` | Max out-degree of any address node |
     | `degree_assortativity` | `nx.degree_assortativity_coefficient()` |
     | `edge_to_node_ratio` | `|E| / |V|` |

   - **Important**: For scenarios with 1-2 txns (most ransomware), many graph features will be trivial (density=1, chain_length=1). This is *correct behavior*, not a bug — it means graph features are discriminative for the rare typologies.

2. **Merge all features** into final feature matrix (~30 min)
   - Concatenate amount + structural + temporal + network + graph features.
   - Save `scenario_features_train_full.csv` and `scenario_features_test_full.csv`.
   - Print feature matrix shape, dtypes, NaN counts.

3. **Train binary classifier v1** (`03_train_binary.py`) (~2 hrs)
   - Features: all columns except `scenario_id`, `is_illicit`, `pattern_type`.
   - Target: `is_illicit`.
   - Model: `XGBClassifier` with:
     ```python
     params = {
         'n_estimators': 500,
         'max_depth': 6,
         'learning_rate': 0.05,
         'subsample': 0.8,
         'colsample_bytree': 0.8,
         'min_child_weight': 5,
         'scale_pos_weight': neg_count / pos_count,  # compute from train
         'eval_metric': 'logloss',
         'early_stopping_rounds': 50,
         'tree_method': 'hist',
         'random_state': 42
     }
     ```
   - Train on `scenario_features_train_full.csv`, evaluate on test split.
   - **Metrics to compute and save**:
     - Classification report (precision, recall, F1 per class).
     - ROC-AUC, PR-AUC.
     - Confusion matrix (plot + save).
     - Calibration curve (pre-calibration).

4. **Probability calibration** (~30 min)
   - Split train into train-proper (80%) + calibration (20%) at scenario level.
   - Train model on train-proper, fit `CalibratedClassifierCV` (isotonic regression, as dataset is large enough) on calibration set.
   - Compare calibration curves before/after.
   - If isotonic improves ECE (Expected Calibration Error), use calibrated model; else use Platt scaling; else use raw.

#### Validation Checks (Gate for Day 3)
- [ ] Binary model test ROC-AUC ≥ 0.85 (sanity — if it's <0.7, something is wrong with features).
- [ ] No single feature has >50% importance share (would suggest shortcut learning).
- [ ] Calibration curve is not wildly off-diagonal.
- [ ] Model saved to `ml/models/binary_xgb_v1.json`.

---

### Day 3 (Sep 4-5): Typology Model + LOSOCV + Ablation

#### Tasks
1. **Typology classifier** (`04_train_typology.py`) (~3 hrs)
   - **Subset**: Only illicit scenarios (train: ~12,965 scenarios).
   - **Target**: `pattern_type` ∈ {ransomware, peeling_chain, layering, mixing}.
   - **Class weights**: Compute `sample_weight` inversely proportional to class frequency.
   
   **Two evaluation tracks**:
   
   **Track A — Fixed split (for ransomware vs rest)**:
   - Train on illicit train scenarios, evaluate on illicit test scenarios.
   - Report per-class precision/recall/F1.
   - This is valid for ransomware (3,225 test scenarios) but NOT for rare typologies.
   
   **Track B — LOSOCV (for rare typologies)**:
   - Pool ALL peeling_chain (32+8=40), layering (20+5=25), mixing (16+4=20) scenarios from both train and test.
   - Also include a *stratified random sample* of 200 ransomware scenarios as the majority class anchor.
   - Run leave-one-out CV: for each rare-typology scenario, train on all others, predict it.
   - Report per-class accuracy, macro-F1, and confusion matrix.
   - **This is the honest evaluation for judges**: "We have 85 rare-pattern scenarios total. LOSOCV gives each one a held-out prediction."

   > [!WARNING]
   > LOSOCV means training the model 85 times (one per rare scenario). With ~285 total scenarios per fold and XGBoost, each fit takes <1 second. Total wall time: ~2-3 minutes. This is tractable.

2. **Ablation study** (`06_ablation.py`) (~2 hrs)
   - Train the binary model under 4 feature configurations:
   
   | Ablation | Features included | Purpose |
   |---|---|---|
   | **Blockchain-only** | Amount + structural + temporal features | Baseline without network layer |
   | **Network-only** | Network-layer features only | Tests the PS's unique premise |
   | **Combined (no graph)** | All non-graph features | Full feature set minus topology |
   | **Full** | All features including graph | Production model |
   
   - Compare ROC-AUC, PR-AUC, and F1 across ablations.
   - **Key result for judges**: Network features should improve AUC by a measurable amount (even 1-3pp matters). If they don't improve anything, the "network layer analysis" premise is empty — flag this as a finding, don't hide it.
   - Save comparison table and bar chart to `outputs/ablation_results.png`.

3. **Feature importance analysis** (~1 hr)
   - XGBoost native `feature_importances_` (gain-based).
   - Rank top-20 features for binary and typology models.
   - Save to `outputs/feature_importance_binary.png` and `outputs/feature_importance_typology.png`.

#### Validation Checks (Gate for Day 4)
- [ ] Typology LOSOCV macro-F1 across rare classes ≥ 0.5 (if <0.3, features are not discriminative enough — revisit feature engineering).
- [ ] Ablation results show the full model outperforms each subset (even marginally).
- [ ] No feature importance is dominated by a single trivial feature (e.g., `num_txns` alone).
- [ ] Models saved: `ml/models/typology_xgb_v1.json`.

---

### Day 4 (Sep 5-6): Explainability + NL Explanation Generation

#### Tasks
1. **SHAP explainability** (`05_explainability.py`) (~3 hrs)
   - **Global explanations** (both models):
     ```python
     import shap
     explainer = shap.TreeExplainer(model)  # TreeSHAP, exact, fast
     shap_values = explainer.shap_values(X_test)
     
     # Summary plot (beeswarm)
     shap.summary_plot(shap_values, X_test, show=False)
     plt.savefig('outputs/shap_summary_binary.png', dpi=150, bbox_inches='tight')
     
     # Bar plot (mean |SHAP|)
     shap.summary_plot(shap_values, X_test, plot_type='bar', show=False)
     plt.savefig('outputs/shap_bar_binary.png', dpi=150, bbox_inches='tight')
     ```
   
   - **Per-candidate explanations**:
     - For each test scenario, compute SHAP values.
     - Identify top-3 contributing features (by absolute SHAP value).
     - Store as structured dict: `{scenario_id, top_features: [{name, value, shap_value, direction}]}`.

2. **Natural-language explanation templates** (~2 hrs)
   - Define template strings per typology:
     ```python
     TEMPLATES = {
         'peeling_chain': (
             "Flagged as likely peeling chain (confidence {conf:.0%}): "
             "detected {chain_length}-hop chain with decreasing amounts "
             "(decay slope {decay_slope:.4f}), {address_reuse:.0%} address reuse "
             "between hops, and tight inter-hop timing (mean {delta_mean:.1f}s). "
             "{net_signal}"
         ),
         'layering': (
             "Flagged as likely layering/fan-out-fan-in (confidence {conf:.0%}): "
             "{fanout_ratio:.1f}x fan-out ratio with {reconvergence} reconvergence "
             "points detected, {unique_outputs} unique output addresses across "
             "{num_txns} transactions. {net_signal}"
         ),
         'mixing': (
             "Flagged as likely mixing cluster (confidence {conf:.0%}): "
             "dense subgraph ({density:.3f}) with near-equal output amounts "
             "(Gini {gini:.3f}), {io_ratio:.2f} I/O count ratio, within a "
             "{time_span:.1f}-hour window. {net_signal}"
         ),
         'ransomware': (
             "Flagged as likely ransomware activity (confidence {conf:.0%}): "
             "{num_txns} transactions with {round_pct:.0%} round-number amounts, "
             "fee consistency (σ={fee_std:.6f}). {net_signal}"
         ),
         'generic_illicit': (
             "Flagged as suspicious (confidence {conf:.0%}). "
             "Top signals: {top1_name} ({top1_dir} {top1_val:.4f}, "
             "SHAP contribution {top1_shap:+.3f}), "
             "{top2_name} ({top2_dir} {top2_val:.4f}), "
             "{top3_name} ({top3_dir} {top3_val:.4f})."
         )
     }
     ```
   - **Logic**: If binary model flags illicit AND typology model has ≥60% confidence in a specific typology → use that typology's template. Else → use `generic_illicit` template with SHAP top-3 features.
   - Network signal suffix (`net_signal`): if `suspicious_infra_ratio > 0.3`, append "Relayed via suspicious infrastructure ({ratio:.0%} Tor/VPN/bulletproof nodes)." Else if `unique_country_count > 3`, append "Geographic dispersion across {n} countries detected."

3. **Build `inference.py`** (~1.5 hrs)
   - Single entry point function:
     ```python
     def predict_scenario(scenario_df: pd.DataFrame, 
                          blockchain_txns: pd.DataFrame,
                          network_meta: pd.DataFrame) -> dict:
         """
         Input: scenario_id's transactions (pre-filtered).
         Output: {
             'scenario_id': str,
             'is_illicit': bool,
             'illicit_confidence': float,  # calibrated
             'typology': str | None,       # None if licit
             'typology_confidence': float | None,
             'explanation': str,           # NL template output
             'shap_features': list[dict],  # top-5 SHAP contributors
         }
         """
     ```
   - Load saved models + calibrator from `ml/models/`.
   - Compute features for input scenario, run both models, generate explanation.
   - **Must run fully offline** — no API calls, no network access.

#### Validation Checks (Gate for Day 5)
- [ ] `inference.py` runs end-to-end on 5 random test scenarios and produces valid output.
- [ ] NL explanations are grammatically correct and mention real feature values.
- [ ] SHAP plots saved and visually interpretable.
- [ ] Calibrated confidence scores: mean predicted probability for truly illicit scenarios is close to the actual positive rate in that probability bin (within 10pp).

---

### Day 5 (Sep 6-7): Hardening + Demo Prep + Integration Handoff

#### Tasks
1. **Model hardening & hyperparameter tuning** (~2 hrs)
   - Run `RandomizedSearchCV` (not Grid — too slow) with 5-fold *group* CV (groups=scenario_id within train split) for the binary model:
     ```python
     param_dist = {
         'max_depth': [4, 5, 6, 7, 8],
         'learning_rate': [0.01, 0.03, 0.05, 0.1],
         'n_estimators': [300, 500, 800],
         'min_child_weight': [3, 5, 10],
         'subsample': [0.7, 0.8, 0.9],
         'colsample_bytree': [0.6, 0.7, 0.8, 0.9],
         'gamma': [0, 0.1, 0.3],
         'reg_alpha': [0, 0.1, 1.0],
         'reg_lambda': [1.0, 3.0, 5.0],
     }
     # n_iter=50, scoring='roc_auc', cv=GroupKFold(5)
     ```
   - Retrain final model with best params on full train split.
   - Re-calibrate probabilities.
   - Re-run SHAP on the tuned model.

2. **Demo result generation** (~1.5 hrs)
   - Run inference on the full test set.
   - Produce:
     - `outputs/demo_results.json` — all test scenario predictions with explanations.
     - `outputs/metrics_summary.md` — final metrics table.
     - `outputs/sample_explanations.md` — 10 cherry-picked examples (2 per typology + 2 normal) showing the NL explanation.
     - `outputs/confusion_matrix_final.png`.
     - `outputs/roc_curve_final.png`.
     - `outputs/shap_summary_final.png`.

3. **Integration handoff to dashboard team** (~1 hr)
   - Write `ml/README.md` documenting:
     - How to call `inference.py`.
     - Expected input/output JSON schemas.
     - Model file locations.
     - Python dependency list.
   - Package models: `ml/models/binary_xgb_final.json`, `ml/models/typology_xgb_final.json`, `ml/models/calibrator.pkl`.
   - Test offline: ensure no network calls during inference (run with `unshare -n` or check imports).

4. **Ablation writeup for judges** (~30 min)
   - Format the ablation comparison into a presentation-ready table.
   - Key narrative: "The combined blockchain + network feature model achieves X% AUC vs Y% with blockchain alone and Z% with network alone, demonstrating that both signal sources contribute to detection capability."

#### Validation Checks (Final)
- [ ] Final binary model test ROC-AUC is at least as good as v1 (no regression from tuning).
- [ ] `inference.py` processes 3,523 test scenarios in <60 seconds total.
- [ ] All output files exist and are non-empty.
- [ ] Model files total <50 MB (XGBoost JSON models are typically <5 MB).
- [ ] Offline validation: `inference.py` runs successfully with network disabled.

---

### Day 6 (Sep 7-8): Buffer / Polish / Integration Support

This day is intentionally unplanned as buffer for:
- Fixing any issues found during dashboard integration.
- Re-running models if P4 delivers graph features late.
- Improving NL explanation templates based on team feedback.
- Adding any last-minute features or metrics the team needs for the demo.
- Creating a "model card" document for the judges if requested.

---

## Risk Registry

Ranked by impact × probability:

| # | Risk | Impact | Probability | Mitigation |
|---|---|---|---|---|
| 🔴 1 | **Typology test set too small for meaningful evaluation** | High | **Confirmed** (5 layering, 4 mixing test scenarios) | LOSOCV on pooled data; frame honestly in presentation; binary model is the primary deliverable |
| 🔴 2 | **P4 doesn't deliver graph features in time** | High | Medium | Fallback: build lightweight networkx graphs from array columns on Day 2. Lose reconvergence and community features but retain degree/chain-length/density |
| 🟡 3 | **Features don't discriminate rare typologies** | Medium | Medium | If LOSOCV macro-F1 <0.3, fall back to binary-only + rule-based typology heuristics as a *post-hoc annotation* (not the model itself — model stays ML) |
| 🟡 4 | **Network features add zero signal** | Medium | Low-Medium | Ablation will reveal this. If true, reframe: "network features provide complementary context for explainability even when not improving classification" |
| 🟢 5 | **Hard-negative exchanges fool the model** | Medium | Low | Check confusion matrix specifically for exchange scenarios. If FP rate on exchanges >20%, add `num_txns`-aware features or a dedicated exchange-detection head |
| 🟢 6 | **SHAP computation too slow** | Low | Low | TreeSHAP on XGBoost is O(TLD²) per sample; with 500 trees, depth 6, ~40 features, ~3,500 test scenarios → <30 seconds. Not a concern. |

---

## Day 1 Priority Checklist (Do These Before Anything Else)

1. **Install missing packages**: `conda install -c conda-forge xgboost shap networkx -y`
2. **Message P4** about graph features (exact question above).
3. **Run the scenario aggregation** and verify the 14,090 / 3,523 scenario counts.
4. **Check the correlation matrix** of raw features vs `is_illicit` — if any single feature has >0.9 correlation, investigate for label leakage before proceeding.
5. **Compute scenario-level binary class balance** — if it's wildly different from the 63/37 transaction-level split, adjust `scale_pos_weight` accordingly.
