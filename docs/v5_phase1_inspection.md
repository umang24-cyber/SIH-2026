# V5 Phase 1 — Inspection & Map

## (a) Confirmed File Inventory

### `data/processed/` (15 files — all generated artifacts, safe to regenerate/archive)
- `blockchain_transactions.csv` (24MB, 84,273 txns + header)
- `network_metadata.csv` (11MB, 84,273 rows + header)
- `train_blockchain.csv` / `test_blockchain.csv` — split raw data
- `train_network.csv` / `test_network.csv` — split raw data
- `scenario_features_train.csv` / `scenario_features_test.csv` — Phase-1 features (39 feature cols + scenario_id)
- `scenario_graph_features_train.csv` / `scenario_graph_features_test.csv` — graph features (7 cols + scenario_id)
- `scenario_features_full_train.csv` / `scenario_features_full_test.csv` — merged (46 feature cols + scenario_id)
- `scenario_labels_train.csv` / `scenario_labels_test.csv` — labels
- `script_type_encoder.json`

### `data_pipeline/` (9 files — source code)
- `generate_v2.py`, `generate_v3.py`, `generate_v4.py` — generator scripts
- `audit_v3.py`, `audit_v4.py` — acceptance audit scripts
- `step4_build_blockchain_table.py`, `step5_build_network_metadata.py` — intermediate pipeline steps
- `validate_pipeline.py`, `validate_v2.py` — validators

### `graph_engine/` (13 files — source code)
- Core: `__init__.py`, `config.py`, `ingest.py`, `graph_build.py`, `features.py`, `structures.py`, `export.py`, `validate.py`, `main.py`
- `requirements.txt`, `README.md`
- `detectors/` — peeling_chain, layering, mixing detector modules
- `tests/`

### `ml/` (9 source files + generated artifacts)
- Pipeline: `01_eda_and_validation.py`, `02_feature_engineering.py`, `02b_graph_features.py`, `02c_merge_features.py`
- Training: `03_train_binary.py`, `04_train_typology.py`, `05_ablation.py`
- Diagnostic: `diag_audit.py`, `full_audit_v3.py`
- `models/` — 5 model artifact files
- `outputs/` — 21 report/chart artifacts

### Unrelated scaffold (out of scope, leave alone)
- `node_modules/`, `src/`, `index.html`, `package.json`, `package-lock.json`, `vite.config.ts`, `tsconfig.json`

---

## (b) The 18-vs-46 Feature Gap Explanation

**Root cause: The v4 audit (`audit_v4.py`) re-derives its own 18-feature scenario aggregates from raw CSV data. It does NOT import or call the ML pipeline's feature functions.**

The v4 audit's `compute_scenario_features()` (lines 139-225) computes 18 features inline:
`num_txns`, `duration_hrs`, `unique_ip_count`, `unique_asn_count`, `unique_country_count`,
`unique_input_addrs`, `unique_output_addrs`, `total_wallets`, `total_amount_btc`,
`mean_amount_btc`, `total_fee_btc`, `fee_ratio`, `txn_velocity`, `mean_inter_tx_sec`,
`graph_nodes`, `graph_edges`, `graph_density`, `pct_susp_node`

It then separately checks 4 derived features: `mean_num_inputs`, `fanin_ratio`, `address_reuse_ratio`, `edge_to_node_ratio` — but only in Gate I's typology check, not in Gates A-C.

**The real ML pipeline** (`02_feature_engineering.py` → `02b_graph_features.py` → `02c_merge_features.py`) produces **46 features**:

Phase-1 (39 features from `02_feature_engineering.py`):
- Amount: `total_input_mean`, `total_output_mean`, `fee_ratio_mean`, `fee_ratio_std`, `amount_decay_slope`, `output_amount_gini`, `denomination_entropy`, `round_number_ratio`, `io_amount_similarity`
- Structural: `num_txns`, `mean_num_inputs`, `mean_num_outputs`, `io_count_ratio`, `unique_input_addrs`, `unique_output_addrs`, `address_reuse_ratio`, `change_output_ratio`, `fanout_ratio`, `fanin_ratio`, `script_type_entropy`, `script_type_mode`
- Temporal: `time_span_hours`, `inter_tx_delta_mean`, `inter_tx_delta_std`, `inter_tx_delta_min`, `burstiness_B`, `hour_of_day_entropy`
- Propagation: `prop_delta_mean`, `prop_delta_std`, `prop_delta_cv`
- Network: `suspicious_infra_ratio`, `unique_asn_count`, `asn_concentration`, `unique_country_count`, `country_concentration`, `unique_ip_count`, `ip_to_addr_ratio`, `alt_port_ratio`, `unique_user_agents`

Graph (7 features from `02b_graph_features.py`):
- `max_chain_length`, `graph_density`, `avg_clustering`, `max_in_degree`, `max_out_degree`, `degree_assortativity`, `edge_to_node_ratio`

**28 features were NEVER checked by the v4 audit's Gates A-C**: The audit missed all amount-derived features (gini, decay slope, denomination entropy, etc.), all temporal-derived features (burstiness, hour entropy, propagation delta CV), all ratio features (io_count_ratio, ip_to_addr_ratio, etc.), and all 7 graph features for the single-feature AUC check.

**Critical**: `address_reuse_ratio` is computed DIFFERENTLY between the audit and the ML pipeline:
- Audit: `1.0 - (total_wallets / (total_in_cnt + total_out_cnt))` 
- ML pipeline: `len(input∩output) / len(output_addrs)` — actual address reuse fraction

This means even for the features they "share", the audit was computing a different quantity.

---

## (c) Graph Engine Compatibility Risk Assessment

**Schema compatibility: PARTIAL — one hard issue, fixable.**

The Graph Engine's `ingest.py` validates against a **hardcoded expected row count** of 82,078 (line 128). The current v4 data has 84,273 rows. Any V5 dataset will also differ. This validation MUST be relaxed or removed for V5.

Otherwise, the schema is fully compatible:
- Expected columns match exactly: `txid`, `timestamp`, `input_addresses`, `output_addresses`, `input_amounts`, `output_amounts`, `fee_btc`, `script_type`, `relay_timestamp`, `relay_ip`, `relay_port`, `node_type`, `country_code`, `asn`, `isp`, `user_agent`
- JSON array parsing is compatible
- Ground-truth columns (`is_illicit`, `pattern_type`, `scenario_id`, `split`) are handled as optional passthrough

**Has it ever been run against v3/v4 data?** The git log shows it was merged from graph branch (`cb9b8af`) but there's no evidence of any output/ directory or generated artifacts. The hardcoded 82,078 row count suggests it was written against an earlier dataset. **This is a real integration risk** — first run will likely error on the row count check.

---

## (d) Contradictions with Part 2 Assumptions

1. **Row count**: Dataset has 84,273 rows (not the 82,078 expected by graph_engine, nor the 83,812 mentioned in the v4 audit report). This suggests the v4 audit's report was written with hardcoded numbers from a different run.
2. **`generate_v4.py` docstring says "v3"**: The file is labeled as v3 internally despite being named v4. The generator appears to be the same code for both v3 and v4 (the "v4" changes may have been noise parameter tweaks, not a separate file).
3. **No `output/` directory exists**: The graph engine was never successfully run against any version of the current data.
4. **`is_licit_exchange` column**: Referenced in FORBIDDEN sets in training scripts but does NOT appear in the current dataset columns. Not a problem — the filter just won't match anything.
