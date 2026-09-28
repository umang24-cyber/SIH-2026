#!/usr/bin/env bash
# Install exclusively from the shipped wheelhouse. No fallback to PyPI.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
if [[ ! -f "$ROOT/dist/index.html" || ! -d "$ROOT/wheelhouse" || ! -f "$ROOT/requirements.lock.txt" || ! -f "$ROOT/bundle-manifest.json" ]]; then
    echo 'Incomplete/unverified offline bundle: dist, wheelhouse, lockfile and bundle-manifest.json are required.' >&2; exit 1
fi
"$PYTHON_BIN" -c 'import sys; assert sys.version_info[:2] in ((3,11),(3,12)), "Use Python 3.11 or 3.12"'
"$PYTHON_BIN" -B "$ROOT/scripts/bundle_manifest.py" "$ROOT" --verify
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then "$PYTHON_BIN" -m venv "$ROOT/.venv"; fi
export PIP_NO_INDEX=1
export PIP_FIND_LINKS="$ROOT/wheelhouse"
"$ROOT/.venv/bin/python" -m pip install --no-compile --no-index --find-links "$ROOT/wheelhouse" -r "$ROOT/requirements.lock.txt"
"$ROOT/.venv/bin/python" -m pip check
PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" "$ROOT/.venv/bin/python" -B -c 'import warnings; from sklearn.exceptions import InconsistentVersionWarning; warnings.filterwarnings("error", category=InconsistentVersionWarning); from backend.app.services.ml_service import ml_service; from backend.app.services.anomaly_service import anomaly_service; ml_service.load_model(); anomaly_service.load_model()'
echo 'Offline environment installed. Start with ./run_ubuntu.sh and open http://127.0.0.1:8000.'
