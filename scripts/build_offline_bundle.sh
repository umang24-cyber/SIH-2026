#!/usr/bin/env bash
# Run ONCE on a connected Linux x86_64 build host matching the target Ubuntu/Python.
# The resulting directory can be carried on USB to an air-gapped machine.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
TARGET="${1:-$ROOT/offline_bundle/BitKaun-linux-x86_64}"

if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    echo 'Build on the target Linux architecture (x86_64).' >&2; exit 1
fi
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] in ((3,11),(3,12)), "Use Python 3.11 or 3.12"'
if [[ -e "$TARGET" ]]; then echo "Target already exists: $TARGET" >&2; exit 1; fi
for file in \
    "$ROOT/data/processed/blockchain_transactions.csv" \
    "$ROOT/data/processed/network_metadata.csv" \
    "$ROOT/ml/manifests/MANIFEST_v8.json" \
    "$ROOT/ml/models/binary_model_v8.ubj" \
    "$ROOT/ml/models/typology_model_v8.ubj" \
    "$ROOT/ml/models/typology_label_encoder.json" \
    "$ROOT/ml/models/anomaly_norm_params.json" \
    "$ROOT/data/processed/script_type_encoder.json"; do
    if [[ ! -s "$file" ]]; then echo "Missing required offline artifact: $file" >&2; exit 1; fi
done
if [[ ! -s "$ROOT/ml/models/anomaly_model_v8.pkl" && ! -s "$ROOT/ml/models/anomaly_model_v7.pkl" ]]; then
    echo 'Missing anomaly model: expected anomaly_model_v8.pkl or anomaly_model_v7.pkl' >&2; exit 1
fi
mkdir -p "$(dirname "$TARGET")"
mkdir -p "$TARGET/wheelhouse" "$TARGET/data"

"$PYTHON_BIN" -m pip download --only-binary=:all: --dest "$TARGET/wheelhouse" -r "$ROOT/backend/requirements.txt" rich requests
"$PYTHON_BIN" -m pip wheel --no-deps --wheel-dir "$TARGET/wheelhouse" "$ROOT/cli"
if [[ "${BITKAUN_USE_PREBUILT_FRONTEND:-0}" == 1 ]]; then
    if [[ ! -s "$ROOT/dist/index.html" ]]; then echo 'Prebuilt frontend requested, but dist/index.html is missing.' >&2; exit 1; fi
else
    (cd "$ROOT" && npm ci && npm run build)
fi

cp -a "$ROOT/backend" "$ROOT/ml" "$ROOT/cli" "$ROOT/graph_engine" "$ROOT/data_pipeline" "$ROOT/docs" "$ROOT/src" "$ROOT/dist" "$ROOT/scripts" "$TARGET/"
cp -a "$ROOT/data/processed" "$TARGET/data/"
cp "$ROOT/data/DATASET_HANDOFF.md" "$TARGET/data/"
if [[ -d "$ROOT/data/processed_v8" ]]; then cp -a "$ROOT/data/processed_v8" "$TARGET/data/"; fi
if [[ -f "$ROOT/public/data/graph_export.json" ]]; then
    mkdir -p "$TARGET/dist/data"
    cp "$ROOT/public/data/graph_export.json" "$TARGET/dist/data/"
fi
cp "$ROOT/run_ubuntu.sh" "$ROOT/GRAPH_ENGINE.md" "$ROOT/DATA_DICTIONARY.md" "$ROOT/DEADLOCK_PROTOCOL.md" "$ROOT/readme.md" "$ROOT/package.json" "$ROOT/vite.config.ts" "$ROOT/requirements.txt" "$TARGET/"
chmod +x "$TARGET/run_ubuntu.sh" "$TARGET/scripts/install_offline.sh"

# Validate the downloaded wheels in a clean environment. Do not ship that venv:
# virtualenv script paths are absolute and cannot be moved to another machine.
VERIFY_ENV="$(mktemp -d)"
trap 'rm -rf "$VERIFY_ENV"' EXIT
"$PYTHON_BIN" -m venv "$VERIFY_ENV"
"$VERIFY_ENV/bin/python" -m pip install --no-compile --no-index --find-links "$TARGET/wheelhouse" -r "$TARGET/backend/requirements.txt" bitkaun
"$VERIFY_ENV/bin/python" -m pip check
"$VERIFY_ENV/bin/python" -B "$TARGET/scripts/verify_offline_runtime.py" > "$TARGET/runtime-verification.json"
"$VERIFY_ENV/bin/python" -m pip freeze > "$TARGET/requirements.lock.txt"
"$VERIFY_ENV/bin/python" -B "$TARGET/scripts/bundle_manifest.py" "$TARGET"
echo "Linux offline bundle ready at: $TARGET"
echo 'Transfer the entire directory to a matching Linux machine, then run ./scripts/install_offline.sh and ./run_ubuntu.sh there.'
