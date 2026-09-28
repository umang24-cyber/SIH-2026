#!/usr/bin/env bash
# Linux runtime: serves the built React/Three.js UI and local API from one process.
# No npm, pip, package registry, cloud call or network access is needed at runtime.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$DIR/dist/index.html" ]]; then
    echo "Missing built frontend: dist/index.html. Use the Linux offline bundle or build on a connected preparation machine." >&2
    exit 1
fi

if [[ -x "$DIR/.venv/bin/python" ]]; then
    PYTHON="$DIR/.venv/bin/python"
elif [[ -n "${CONDA_PREFIX:-}" && -x "$CONDA_PREFIX/bin/python" ]]; then
    PYTHON="$CONDA_PREFIX/bin/python"
else
    echo "No provisioned Python environment. On Linux run ./scripts/install_offline.sh with the included wheelhouse." >&2
    exit 1
fi

if ! "$PYTHON" -c 'import fastapi, uvicorn, numpy, pandas, xgboost, sklearn, shap, multipart' >/dev/null 2>&1; then
    echo "Local Python environment is missing backend dependencies. Run ./scripts/install_offline.sh." >&2
    exit 1
fi

export PYTHONPATH="$DIR${PYTHONPATH:+:$PYTHONPATH}"
echo "BitKaun offline: open http://127.0.0.1:8000 (API reference: /docs)"
exec "$PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
