import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "ml" / "models"

# Ensure v8 models exist
pairs = [
    ("binary_model_v7_candidate.ubj", "binary_model_v8.ubj"),
    ("binary_model_v7_candidate.xgb", "binary_model_v8.xgb"),
    ("typology_model_v7_candidate.ubj", "typology_model_v8.ubj"),
    ("typology_model_v7_candidate.xgb", "typology_model_v8.xgb"),
    ("anomaly_model_v7.pkl", "anomaly_model_v8.pkl")
]

for src, dst in pairs:
    src_path = MODELS_DIR / src
    dst_path = MODELS_DIR / dst
    if src_path.exists():
        shutil.copy2(src_path, dst_path)
        print(f"Copied {src} -> {dst}")
    else:
        print(f"Source not found: {src}")

print("V8 Model Artifacts Setup Complete.")
