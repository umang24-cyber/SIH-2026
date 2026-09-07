#!/bin/bash
set -e
source /home/param/miniforge3/etc/profile.d/conda.sh
conda activate ml

echo "Running 02_feature_engineering_v8.py"
python ml/02_feature_engineering_v8.py

echo "Running 02b_graph_features_v8.py"
python ml/02b_graph_features_v8.py

echo "Running 02c_merge_features_v8.py"
python ml/02c_merge_features_v8.py

echo "Running train_v8.py"
python ml/train_v8.py

echo "V8 ML Pipeline Complete."
