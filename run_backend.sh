#!/usr/bin/env bash
# ==============================================================================
# BitKaun AML Forensics API - Offline Linux / WSL2 Startup Script
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "  BitKaun AML Forensics Platform — Backend Server Startup"
echo "  Mode: 100% Offline / Air-Gapped Linux (WSL2 / Ubuntu 24.04 LTS)"
echo "================================================================="

# Source conda and activate ml environment
if [ -f "/home/param/miniforge3/etc/profile.d/conda.sh" ]; then
    source "/home/param/miniforge3/etc/profile.d/conda.sh"
    conda activate ml
fi

# Export PYTHONPATH to include project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run Uvicorn server on localhost:8000
echo "[+] Starting FastAPI server on http://0.0.0.0:8000 ..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend/app
