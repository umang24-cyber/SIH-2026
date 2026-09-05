"""
ML Model Inference & Feature Extraction Hook.
Provides seamless drop-in integration for trained ML models (LightGBM, XGBoost, Scikit-learn).
Runs 100% offline in-memory without external calls.
"""
import os
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
from backend.app.core.config import BASE_DIR

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path(__file__).resolve().parent.parent / "models" / "weights"
DEFAULT_MODEL_PATH = WEIGHTS_DIR / "model.pkl"
ML_DIR_MODELS = Path(__file__).resolve().parent.parent.parent.parent / "ml" / "models"

class MLService:
    def __init__(self):
        self.model = None
        self.typology_model = None
        self.label_encoder_classes = []
        self.is_loaded = False
        self._ensure_weights_dir()

    def _ensure_weights_dir(self):
        """Ensure weights directory exists for the user to drop models into."""
        WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
        readme_path = WEIGHTS_DIR / "README.md"
        if not readme_path.exists():
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(
                    "# ML Model Weights Drop-in Directory\n\n"
                    "Drop your trained `model.pkl` or `binary_model_v6.xgb` file here.\n"
                    "The backend will automatically detect, load, and use it for live inference on `/alerts`.\n"
                )

    def load_model(self, model_path: Optional[Path] = None):
        """Loads serialized XGBoost / Pickle model from weights or ml/models directory."""
        # Check priority paths
        candidates = []
        if model_path:
            candidates.append(model_path)
        candidates.extend([
            WEIGHTS_DIR / "model.pkl",
            WEIGHTS_DIR / "binary_model_v6.xgb",
            ML_DIR_MODELS / "binary_model_v6.xgb",
            ML_DIR_MODELS / "binary_xgb_v1.json"
        ])

        for p in candidates:
            if p.exists():
                try:
                    if str(p).endswith(".xgb") or str(p).endswith(".json"):
                        import xgboost as xgb
                        self.model = xgb.XGBClassifier()
                        self.model.load_model(str(p))
                    else:
                        with open(p, "rb") as f:
                            self.model = pickle.load(f)
                    self.is_loaded = True
                    logger.info(f"Successfully loaded trained ML model from: {p}")
                    break
                except Exception as e:
                    logger.warning(f"Could not load ML model from {p}: {e}")

        # Check typology model
        typ_path = ML_DIR_MODELS / "typology_model_v6.xgb"
        if typ_path.exists():
            try:
                import xgboost as xgb
                self.typology_model = xgb.XGBClassifier()
                self.typology_model.load_model(str(typ_path))
                logger.info(f"Successfully loaded typology ML model from: {typ_path}")
            except Exception as e:
                logger.warning(f"Could not load typology model: {e}")

        if not self.is_loaded:
            logger.info("Operating in Heuristic Fallback mode (Ready to drop model weights).")

    def extract_features(self, tx_record: Dict[str, Any]) -> np.ndarray:
        """
        Extracts feature vector from transaction record adhering to DATA_DICTIONARY.md Section 8a.
        Excludes is_illicit, pattern_type, scenario_id, split (Zero Leakage Invariant).
        """
        in_amts = tx_record.get("input_amounts", [0.0])
        out_amts = tx_record.get("output_amounts", [0.0])
        fee = float(tx_record.get("fee_btc", 0.0))
        tot_in = sum(in_amts)
        tot_out = sum(out_amts)

        # 1. Financial Features
        num_inputs = len(in_amts)
        num_outputs = len(out_amts)
        fee_ratio = fee / max(0.00001, tot_in)
        avg_output_btc = tot_out / max(1, num_outputs)

        # 2. Timing Delta (Dual-Layer P2P)
        propagation_delta_ms = float(tx_record.get("propagation_delta_ms", 0.0))

        # 3. Script Type One-Hot
        st = str(tx_record.get("script_type", "P2PKH"))
        is_p2pkh = 1 if st == "P2PKH" else 0
        is_p2sh = 1 if st == "P2SH" else 0
        is_p2wpkh = 1 if st == "P2WPKH" else 0

        # 4. Node Type One-Hot
        nt = str(tx_record.get("node_type", "residential"))
        is_bulletproof = 1 if nt == "bulletproof_host" else 0
        is_tor = 1 if nt == "tor_exit_node" else 0
        is_vpn = 1 if nt == "vpn_proxy" else 0
        is_datacenter = 1 if nt == "datacenter" else 0

        features = [
            tot_in,
            tot_out,
            fee,
            num_inputs,
            num_outputs,
            fee_ratio,
            avg_output_btc,
            propagation_delta_ms,
            is_p2pkh,
            is_p2sh,
            is_p2wpkh,
            is_bulletproof,
            is_tor,
            is_vpn,
            is_datacenter
        ]
        return np.array(features, dtype=np.float32).reshape(1, -1)

    def predict_risk(self, target: Any) -> Dict[str, Any]:
        """
        Predicts illicit probability for a transaction.
        Accepts either a txid (int/str) or a transaction record dictionary.
        Uses trained ML model if loaded; otherwise returns heuristic score.
        """
        if isinstance(target, (int, str)):
            from backend.app.services.data_service import data_service
            tx_record = data_service.txid_map.get(target)
            if not tx_record:
                return {
                    "risk_score": 0.15,
                    "is_illicit": False,
                    "confidence": 0.5,
                    "model_used": "unknown"
                }
        elif isinstance(target, dict):
            tx_record = target
        else:
            return {
                "risk_score": 0.15,
                "is_illicit": False,
                "confidence": 0.5,
                "model_used": "unknown"
            }

        score = 0.15
        model_name = "heuristic"

        if self.is_loaded and self.model is not None:
            try:
                feat = self.extract_features(tx_record)
                if hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba(feat)
                    score = float(probs[0][1])
                    model_name = "xgboost"
                elif hasattr(self.model, "predict"):
                    preds = self.model.predict(feat)
                    score = float(preds[0])
                    model_name = "xgboost"
            except Exception as e:
                logger.warning(f"Inference error with custom model: {e}")
                score = 0.15

        if model_name == "heuristic":
            # Heuristic fallback risk calculation
            nt = tx_record.get("node_type", "residential")
            lat = float(tx_record.get("propagation_delta_ms", 0.0))
            base_risk = 0.85 if nt in ["bulletproof_host", "tor_exit_node"] else 0.15
            if lat > 150:
                base_risk += 0.10
            score = min(0.99, max(0.01, base_risk))

        return {
            "risk_score": round(float(score), 4),
            "is_illicit": bool(score >= 0.5),
            "confidence": round(float(abs(score - 0.5) * 2), 4),
            "model_used": model_name
        }

# Global Singleton Instance
ml_service = MLService()
