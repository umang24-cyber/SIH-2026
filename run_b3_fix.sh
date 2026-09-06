#!/bin/bash
set -e
cd /home/param/SIH-2026
echo "Running graph features..."
conda run -n ml python ml/02b_graph_features.py
echo "Merging features..."
conda run -n ml python ml/02c_merge_features.py
echo "Running training..."
conda run -n ml python ml/train_production.py
echo "Running audit..."
conda run -n ml python data_pipeline/audit_v7.py
echo "Pipeline finished!"
