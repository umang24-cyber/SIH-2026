"""
ML Model Inference & Feature Extraction Hook for V7 Scenario Models.
Runs 100% offline in-memory without external calls.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
from backend.app.core.config import BASE_DIR

# Import V7 Canonical Feature Engineering
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
from ml.02_feature_engineering import compute_scenario_features
from ml.02b_graph_features import compute_graph_features

logger = logging.getLogger(__name__)

ML_DIR_MODELS = BASE_DIR / "ml" / "models"
MANIFEST_PATH = BASE_DIR / "ml" / "manifests" / "MANIFEST_v7_candidate.json"
ENCODER_PATH = BASE_DIR / "data" / "processed" / "script_type_encoder.json"

class MLService:
    def __init__(self):
        self.model = None
        self.typology_model = None
        self.is_loaded = False
        self.feature_names = []
        self.script_type_encoder = {}
        
    def load_model(self):
        """Loads serialized XGBoost models and metadata for V7."""
        # Load manifest to get exact feature order
        if MANIFEST_PATH.exists():
            with open(MANIFEST_PATH, "r") as f:
                manifest = json.load(f)
                self.feature_names = manifest.get("feature_names", [])
        
        # Load encoder
        if ENCODER_PATH.exists():
            with open(ENCODER_PATH, "r") as f:
                self.script_type_encoder = json.load(f)

        # Load Binary Model
        binary_path = ML_DIR_MODELS / "binary_model_v7_candidate.xgb"
        if binary_path.exists():
            try:
                import xgboost as xgb
                self.model = xgb.XGBClassifier()
                self.model.load_model(str(binary_path))
                self.is_loaded = True
                logger.info(f"Successfully loaded V7 binary model from: {binary_path}")
            except Exception as e:
                logger.warning(f"Could not load binary model: {e}")

        # Load Typology Model
        typ_path = ML_DIR_MODELS / "typology_model_v7_candidate.xgb"
        if typ_path.exists():
            try:
                import xgboost as xgb
                self.typology_model = xgb.XGBClassifier()
                self.typology_model.load_model(str(typ_path))
                logger.info(f"Successfully loaded V7 typology model from: {typ_path}")
            except Exception as e:
                logger.warning(f"Could not load typology model: {e}")

    def extract_features(self, scenario_txs: List[Dict[str, Any]]) -> np.ndarray:
        """
        Extracts V7 scenario-level feature vector from a list of transaction records.
        Calls the exact functions from the ml pipeline.
        """
        grp = pd.DataFrame(scenario_txs)
        
        # Ensure timestamp is datetime
        grp["timestamp"] = pd.to_datetime(grp["timestamp"])
        if "relay_timestamp" in grp.columns:
            grp["relay_timestamp"] = pd.to_datetime(grp["relay_timestamp"])
            
        # Parse arrays if they are strings (they should already be lists in memory, but just in case)
        for col in ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]:
            if len(grp) > 0 and isinstance(grp[col].iloc[0], str):
                grp[col] = grp[col].apply(json.loads)

        # 1. Base Features
        base_feats = compute_scenario_features(grp)
        
        # Apply script type encoder
        raw_mode = base_feats.pop("_script_type_mode_raw", "P2PKH")
        base_feats["script_type_mode"] = self.script_type_encoder.get(raw_mode, 0)
        
        # 2. Graph Features
        graph_feats = compute_graph_features(grp)
        graph_feats.pop("_cycle_detected", None)
        
        # 3. Merge and Align
        merged = {**base_feats, **graph_feats}
        
        # Build array in manifest order
        features = []
        for fn in self.feature_names:
            features.append(merged.get(fn, 0.0))
            
        return np.array(features, dtype=np.float32).reshape(1, -1)

    def predict_risk(self, target: Any) -> Dict[str, Any]:
        """
        Predicts illicit probability for a scenario containing the target txid.
        """
        if not self.is_loaded:
            self.load_model()
            
        from backend.app.services.data_service import data_service
        
        tx_records = []
        scenario_id = None
        
        if isinstance(target, (int, str)):
            tx_record = data_service.txid_map.get(target)
            if not tx_record:
                return {"risk_score": 0.0, "is_illicit": False, "confidence": 0.0, "model_used": "unknown"}
            
            scenario_id = tx_record.get("scenario_id")
            if scenario_id:
                txids = data_service.scenario_tx_map.get(scenario_id, [])
                tx_records = [data_service.txid_map[tid] for tid in txids if tid in data_service.txid_map]
            else:
                tx_records = [tx_record]
                
        elif isinstance(target, list):
            tx_records = target
        else:
            tx_records = [target]

        score = 0.15
        model_name = "heuristic"
        typology = "normal"

        if self.is_loaded and self.model is not None and len(tx_records) > 0:
            try:
                feat = self.extract_features(tx_records)
                
                # Binary Prediction
                probs = self.model.predict_proba(feat)
                score = float(probs[0][1])
                model_name = "xgboost_v7"
                
                is_illicit = bool(score >= 0.5)
                
                # Typology Prediction (only if illicit)
                if is_illicit and self.typology_model is not None:
                    typ_preds = self.typology_model.predict(feat)
                    # Need label decoder if applicable (V7 uses LabelEncoder, assume direct string output or mapping)
                    # Let's check typology_label_encoder.json if it exists
                    from backend.app.core.config import BASE_DIR
                    enc_path = BASE_DIR / "ml" / "models" / "typology_label_encoder.json"
                    if enc_path.exists():
                        with open(enc_path, "r") as f:
                            typ_map = {int(v): k for k, v in json.load(f).items()}
                        typology = typ_map.get(int(typ_preds[0]), "unknown")
                    else:
                        typology = "predicted_illicit"
            except Exception as e:
                logger.warning(f"Inference error with custom model: {e}")
                score = 0.15
                is_illicit = False

        return {
            "risk_score": round(float(score), 4),
            "is_illicit": is_illicit,
            "confidence": round(float(abs(score - 0.5) * 2), 4),
            "model_used": model_name,
            "scenario_id": scenario_id,
            "typology": typology
        }

# Global Singleton Instance
ml_service = MLService()
