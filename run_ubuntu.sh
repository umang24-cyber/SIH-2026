#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# 1. Activate environment
if [ -f "/home/param/miniforge3/etc/profile.d/conda.sh" ]; then
    source /home/param/miniforge3/etc/profile.d/conda.sh
    conda activate ml
elif [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "[+] Using active conda environment: $CONDA_DEFAULT_ENV"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[!] Virtualenv not found, creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r backend/requirements.txt
    pip install -r requirements.txt
    pip install -e ./cli
fi

export PYTHONPATH="$DIR:$PYTHONPATH"

echo "================================================================="
echo "  BitKaun AML Forensics Platform — Linux / Ubuntu Launcher"
echo "  FastAPI Backend (Port 8000) + React Frontend (Port 5173)"
echo "================================================================="

cleanup() {
    echo ""
    echo "[+] Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "[1/2] Starting Backend API on http://localhost:8000 ..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "[2/2] Starting Frontend Visualizer on http://localhost:5173 ..."
npm run dev -- --host
