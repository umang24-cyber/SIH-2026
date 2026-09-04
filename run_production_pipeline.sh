#!/bin/bash
set -eo pipefail

echo "=================================================="
echo " SIH-2026 AML PRODUCTION PIPELINE (V6 FROZEN) "
echo "=================================================="

# Enforce strict error handling
export PYTHONHASHSEED=42
V6_RAW_BLOCKCHAIN="data/processed/train_blockchain.csv"
V6_FEAT_TRAIN="data/processed/scenario_features_train.csv"
V6_GRAPH_TRAIN="data/processed/scenario_graph_features_train.csv"

# Validate V6 inputs exist
if [ ! -f "$V6_RAW_BLOCKCHAIN" ]; then
    echo "[FAIL] Missing raw V6 blockchain data: $V6_RAW_BLOCKCHAIN"
    exit 1
fi
if [ ! -f "$V6_FEAT_TRAIN" ]; then
    echo "[FAIL] Missing V6 scenario features: $V6_FEAT_TRAIN"
    exit 1
fi
if [ ! -f "$V6_GRAPH_TRAIN" ]; then
    echo "[FAIL] Missing V6 graph features: $V6_GRAPH_TRAIN"
    exit 1
fi

# Ensure no ambiguous files
if ls data/processed/V4_* 1> /dev/null 2>&1; then
    echo "[FAIL] Found stale V4 files in data/processed/. Quitting to prevent ambiguous consumption."
    exit 1
fi

echo "[PASS] V6 Frozen Data Paths Confirmed."
echo "Execution Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Create required directories
mkdir -p ml/models ml/reports ml/manifests ml/logs

# Run production script
echo "Running ml/train_production.py..."
conda run -n ml python ml/train_production.py | tee ml/logs/train_production.log

# Verify outputs
if [ ! -f "ml/models/binary_model_v6.xgb" ]; then
    echo "[FAIL] Production training failed to produce binary_model_v6.xgb."
    exit 1
fi

echo "=================================================="
echo " PRODUCTION PIPELINE COMPLETED SUCCESSFULLY "
echo "=================================================="
