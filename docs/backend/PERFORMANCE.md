# Startup and first alert request

## Root causes found

- Startup loads/parses ~295k ledger/network rows, then builds wallet/scenario indexes. The old `DataFrame.to_dict('records')` also boxed hundreds of thousands of redundant pandas timestamp objects and materialized a complete intermediate list.
- `/alerts?limit=10` means **return the top ten after ranking the whole dataset**. Previously the first request computed graph/financial/network features, invoked binary/typology models, computed both SHAP explanations and invoked Isolation Forest separately for thousands of scenarios. The limit never limited the scan.
- The old cache lived only in memory and used scenario names without validating changed input. Restarting lost the feature work. Simultaneous alerts/log/dossier requests could launch overlapping scans.

## Changes

1. Startup uses tuple iteration, excludes parser-only datetime helper columns from runtime records, and logs per-phase startup timings.
2. Identical feature mathematics runs faster: tuple iteration replaces per-row pandas Series creation; denomination checks are vectorized; the bounded cycle-BFS stops at its exact depth bound and uses a deque.
3. All valid scenario feature vectors are scored in batched XGBoost/IsolationForest calls. Same classifiers, same feature order, same thresholds and ranking.
4. Binary/typology SHAP is computed only for the returned page or requested evidence. It is cached in memory for subsequent views. Full detail is still returned when requested; classifier labels/scores are not fabricated.
5. Numeric features are cached locally at `<BitKaun app data>/scenario_features.sqlite3`. A SHA-256 key covers the raw feature inputs, extractor/service source, library versions, feature order and encoder. Labels are excluded. Changed inputs/code/schema/environment recompute their features. Predictions are not read from static benchmark reports.
6. A scan lock makes concurrent consumers share one scan. Uploads increment the dataset revision and invalidate ranked results; unchanged input features can still be reused. Dataset mutation detected during a scan fails that attempt rather than publishing mixed results.
7. `GET /alerts/scan-status` exposes `state`, `phase`, `processed`, `total` and `elapsed_seconds` without waiting for the scan lock. The frontend polls it while an alerts command is pending and stops when the command finishes.

## Measured on this checkout (Windows, same 294,693 bundled transactions)

| Operation | Before | After |
| --- | ---: | ---: |
| Dataset loading + indexing | 55.71 s | 24.06 s (17.73 s in subsequent run) |
| First `alerts --limit 10`, empty feature cache | 289.18 s | 181.33 s |
| First alerts after a backend restart, matching disk cache | Full scan again | 8.08 s |
| Repeated alerts in the same process | ~0.002 s | ~0.005 s |

The comparison checked **all 2,253 alert scores, labels and first-page ordering exactly**, and all raw feature vectors to `1e-12` tolerance. File-system caching/hardware load affect timings; these numbers are measurements, not latency guarantees. The first-ever feature-cache build still requires processing every scenario and can take minutes. Once it completes, normal restarts no longer recompute unchanged graph features.

The filesystem matters: in WSL, source/venvs under `/mnt/c` can load Python packages much more slowly than native Linux storage. For the Linux demo, copy the offline bundle to the Linux filesystem before installing its `.venv`.

## Reproduce

```bash
# Supply different output names; do not overwrite your baseline.
BITKAUN_DATA_DIR=/tmp/bitkaun-perf python -B scripts/profile_backend_runtime.py --output /tmp/cold.json
BITKAUN_DATA_DIR=/tmp/bitkaun-perf python -B scripts/profile_backend_runtime.py --output /tmp/warm.json --compare /tmp/cold.json
```

`BITKAUN_FEATURE_CACHE=0` disables persistent feature caching for diagnosis. Normal operation leaves it enabled. Do not delete the forensic database to clear a cache; only the separate `scenario_features.sqlite3` file is a performance cache.
