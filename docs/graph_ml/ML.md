# Machine Learning, Feature Engineering & Explainability Specification

> **Owner:** P5 (ML Engineer)  
> **Source of Truth Reference:** [DATA_DICTIONARY.md](file:///c:/Users/arora/SIH/SIH-2026/DATA_DICTIONARY.md) (Sections 3, 4, 8a) · [API_CONTRACT.md](file:///c:/Users/arora/SIH/SIH-2026/docs/API_CONTRACT.md)

---

## 1. Feature Safety & Ground-Truth Exclusion Invariant

> ### ⚠️ HARD SYSTEM CONSTRAINT: ZERO LABEL LEAKAGE
> Under no circumstances may ground-truth label columns or split keys be used as features in the model.
>
> **Mandatory Feature Drop List:**
> - `is_illicit` (Binary ground-truth target)
> - `pattern_type` (Multiclass ground-truth target)
> - `scenario_id` (Used strictly for group cross-validation)
> - `split` (Used strictly for train/test evaluation partitioning)
>
> P5 must enforce an automated assertion in the feature extraction pipeline:
> ```python
> FORBIDDEN_COLUMNS = {"is_illicit", "pattern_type", "scenario_id", "split"}
> assert not any(c in feature_df.columns for c in FORBIDDEN_COLUMNS), "Label leakage detected in feature matrix!"
> ```

---

## 2. Feature Groups (Per `DATA_DICTIONARY.md` Section 8a)

| Feature Group | Source Columns | Engineered Features | Description |
|---|---|---|---|
| **Transaction Amounts** | `input_amounts`, `output_amounts`, `fee_btc` | `total_input_btc`, `total_output_btc`, `fee_ratio` (`fee_btc / total_input_btc`), `num_inputs`, `num_outputs`, `mean_output_btc`, `std_output_btc` | Financial volume, UTXO fan-out/fan-in counts, and relative miner fee urgency. |
| **Script Type** | `script_type` | One-hot encoded: `script_is_P2PKH`, `script_is_P2SH`, `script_is_P2WPKH`, `script_is_P2WSH` | Identifies legacy vs SegWit address formats. |
| **Timing Telemetry** | `timestamp`, `relay_timestamp` | `propagation_delta_ms` = `(timestamp - relay_timestamp)` in milliseconds, `hour_of_day`, `day_of_week` | Latency between P2P broadcast and block confirmation. |
| **Network Metadata** | `node_type`, `country_code`, `asn`, `isp` | Categorical encodings (One-Hot / Target / Frequency) for `node_type` (`residential`, `datacenter`, `tor_exit_node`, `vpn_proxy`, `bulletproof_host`, `mobile`), high-risk ASN indicator, country frequency | Captures infrastructure risk profile. (Decorrelated reference pools prevent artificial shortcuts). |
| **Graph Topological Metrics** | Output of Graph Module (P4) | `in_degree`, `out_degree`, `pagerank_score`, `clustering_coefficient`, `is_exchange_neighbor` | Topological positioning in transaction web. |

---

## 3. Train / Test Strategy & Evaluation Protocol

### 3.1 Pre-Split Files (Do Not Re-Split)
The dataset already provides pre-stratified 80/20 train and test split files:
- `data/processed/train_blockchain.csv` & `data/processed/train_network.csv` (65,659 rows, 36.6% illicit)
- `data/processed/test_blockchain.csv` & `data/processed/test_network.csv` (16,419 rows, 36.6% illicit)

**Rules:**
- All model training, hyperparameter tuning, and threshold selection must occur strictly on the `train` split.
- The `test` split is evaluated once at the end as an un-leaked benchmark test set.
- Within `train`, cross-validation must use **`GroupKFold(n_splits=5)`** grouped on `scenario_id` to prevent intra-scenario leakage.

---

## 4. Class Imbalance Handling

### Distribution Summary
- `normal` (licit): 52,011 rows (63.4%)
- `ransomware` (illicit): 29,545 rows (36.0%)
- `peeling_chain` (illicit typology): 309 rows (0.38%)
- `layering` (illicit typology): 123 rows (0.15%)
- `mixing` (illicit typology): 90 rows (0.11%)

### Strategies Under Evaluation **[TODO: P5 Decision]**
1. **Cost-Sensitive Learning:** Compute inverse class frequency weights (`scale_pos_weight` in XGBoost, `class_weight='balanced'` in LightGBM).
2. **Two-Stage Hierarchical Model:**
   - *Stage 1:* Binary classifier distinguishing `licit` (normal) vs `illicit` (all threat classes).
   - *Stage 2:* Multiclass typology classifier or heuristic ensemble for flagged illicit transactions.
3. **Focal Loss:** Penalize easy negative examples to focus on difficult minority typologies.

---

## 5. Explainability with SHAP (TreeExplainer)

For every candidate alert generated, the ML pipeline computes local SHAP values to produce a human-readable forensic justification:

```python
import shap

# Compute SHAP values for top predictions
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_candidate)

# Generate top positive/negative risk contributors
# Format attributions into JSON matching API_CONTRACT.md /alerts/{id}/evidence
```

---

## 6. Open ML Decisions & Action Items

- `[ ]` **[TODO: P5]** Add safety assertion unit test `test_ml_safety.py` enforcing feature drop list.
- `[ ]` **[TODO: P5]** Finalize class imbalance resolution (Two-Stage Model vs Class-Weighted Multiclass LightGBM).
- `[ ]` **[TODO: P5]** Package SHAP explanation generator for backend integration into `/alerts/{candidate_id}/evidence`.
