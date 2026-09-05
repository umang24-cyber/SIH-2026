"""
ML model loading, V7 feature extraction, inference, and explanations.

The persisted V7 manifest is the single source of truth for model paths and
feature order. This module imports feature modules only for reusable functions;
their CLI pipelines are guarded and never run here.
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.app.core.config import BASE_DIR

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

compute_scenario_features = importlib.import_module(
    "ml.02_feature_engineering"
).compute_scenario_features
compute_graph_features = importlib.import_module(
    "ml.02b_graph_features"
).compute_graph_features

logger = logging.getLogger(__name__)

ML_DIR_MODELS = BASE_DIR / "ml" / "models"
MANIFEST_PATH = BASE_DIR / "ml" / "manifests" / "MANIFEST_v7_candidate.json"
ENCODER_PATH = BASE_DIR / "data" / "processed" / "script_type_encoder.json"
TYPOLOGY_ENCODER_PATH = ML_DIR_MODELS / "typology_label_encoder.json"
FORBIDDEN_FEATURES = {
    "is_illicit",
    "pattern_type",
    "split",
    "scenario_id",
    "is_licit_exchange",
}


class MLService:
    def __init__(self):
        self.model = None
        self.typology_model = None
        self.is_loaded = False
        self.feature_names: List[str] = []
        self.script_type_encoder: Dict[str, int] = {}
        self.typology_classes: List[str] = []

    @staticmethod
    def _read_json(path: Path, description: str) -> Dict[str, Any]:
        if not path.exists():
            raise RuntimeError(f"Missing {description}: {path}")
        try:
            with path.open("r") as handle:
                value = json.load(handle)
        except Exception as exc:
            raise RuntimeError(f"Could not read {description} at {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise RuntimeError(f"{description} must contain a JSON object: {path}")
        return value

    @staticmethod
    def _model_feature_count(model: Any, description: str) -> int:
        try:
            return int(model.get_booster().num_features())
        except Exception as exc:
            raise RuntimeError(f"Could not inspect {description} feature count: {exc}") from exc

    def _load_typology_classes(self) -> List[str]:
        encoder = self._read_json(TYPOLOGY_ENCODER_PATH, "typology label encoder")
        classes = encoder.get("classes")
        if not isinstance(classes, list) or not classes or not all(isinstance(c, str) for c in classes):
            raise RuntimeError(
                "Typology label encoder must have a non-empty string 'classes' list"
            )
        if len(set(classes)) != len(classes):
            raise RuntimeError("Typology label encoder contains duplicate classes")
        return classes

    def load_model(self):
        """Load and validate the complete V7 inference artifact set."""
        if self.is_loaded:
            return

        manifest = self._read_json(MANIFEST_PATH, "V7 model manifest")
        feature_names = manifest.get("feature_names")
        feature_count = manifest.get("feature_count")
        if not isinstance(feature_names, list) or not feature_names or not all(
            isinstance(name, str) for name in feature_names
        ):
            raise RuntimeError("Manifest feature_names must be a non-empty string list")
        if feature_count != len(feature_names):
            raise RuntimeError(
                f"Manifest feature_count={feature_count} but has {len(feature_names)} feature_names"
            )
        forbidden = sorted(set(feature_names) & FORBIDDEN_FEATURES)
        if forbidden:
            raise RuntimeError(f"Forbidden model features in manifest: {forbidden}")

        binary_name = manifest.get("binary_model")
        typology_name = manifest.get("typology_model")
        if not isinstance(binary_name, str) or not isinstance(typology_name, str):
            raise RuntimeError("Manifest must specify binary_model and typology_model filenames")
        binary_path = ML_DIR_MODELS / binary_name
        typology_path = ML_DIR_MODELS / typology_name
        if not binary_path.exists() or not typology_path.exists():
            raise RuntimeError(
                f"Manifest model files missing: binary={binary_path}, typology={typology_path}"
            )

        try:
            import xgboost as xgb
        except Exception as exc:
            raise RuntimeError(f"XGBoost is required to load V7 models: {exc}") from exc

        binary_model = xgb.XGBClassifier()
        typology_model = xgb.XGBClassifier()
        try:
            binary_model.load_model(str(binary_path))
        except Exception as exc:
            raise RuntimeError(f"Could not load binary V7 model {binary_path}: {exc}") from exc
        try:
            typology_model.load_model(str(typology_path))
        except Exception as exc:
            raise RuntimeError(f"Could not load typology V7 model {typology_path}: {exc}") from exc

        binary_features = self._model_feature_count(binary_model, "binary V7 model")
        typology_features = self._model_feature_count(typology_model, "typology V7 model")
        if binary_features != len(feature_names):
            raise RuntimeError(
                f"Binary model has {binary_features} features but manifest has {len(feature_names)}"
            )
        if typology_features != len(feature_names):
            raise RuntimeError(
                f"Typology model has {typology_features} features but manifest has {len(feature_names)}"
            )

        classes = self._load_typology_classes()
        model_classes = getattr(typology_model, "n_classes_", None)
        if model_classes != len(classes):
            raise RuntimeError(
                f"Typology encoder has {len(classes)} classes but model exposes {model_classes}"
            )

        script_encoder = self._read_json(ENCODER_PATH, "script type encoder")
        if not script_encoder or any(not isinstance(value, int) for value in script_encoder.values()):
            raise RuntimeError("Script type encoder must map labels to integer codes")

        # Assign only after every validation passes.
        self.model = binary_model
        self.typology_model = typology_model
        self.feature_names = feature_names
        self.typology_classes = classes
        self.script_type_encoder = {str(key): int(value) for key, value in script_encoder.items()}
        self.is_loaded = True
        logger.info(
            "Loaded V7 models: binary=%s, typology=%s, features=%d, typology_classes=%s",
            binary_path,
            typology_path,
            len(feature_names),
            classes,
        )

    def _feature_dict(self, scenario_txs: List[Dict[str, Any]]) -> Dict[str, float]:
        if not scenario_txs:
            raise ValueError("At least one transaction is required for feature extraction")

        grp = pd.DataFrame(scenario_txs)
        grp["timestamp"] = pd.to_datetime(grp["timestamp"])
        if "relay_timestamp" in grp.columns:
            grp["relay_timestamp"] = pd.to_datetime(grp["relay_timestamp"])

        for col in ["input_addresses", "output_addresses", "input_amounts", "output_amounts"]:
            if isinstance(grp[col].iloc[0], str):
                grp[col] = grp[col].apply(json.loads)

        base_feats = compute_scenario_features(grp)
        raw_mode = base_feats.pop("_script_type_mode_raw", "P2PKH")
        base_feats["script_type_mode"] = self.script_type_encoder.get(raw_mode, 0)

        graph_feats = compute_graph_features(grp)
        graph_feats.pop("_cycle_detected", None)
        merged = {**base_feats, **graph_feats}
        missing = [name for name in self.feature_names if name not in merged]
        if missing:
            raise RuntimeError(f"Feature extraction did not produce manifest features: {missing}")
        return {name: float(merged[name]) for name in self.feature_names}

    def extract_features(self, scenario_txs: List[Dict[str, Any]]) -> np.ndarray:
        """Extract a V7 feature matrix in canonical manifest order."""
        values = self._feature_dict(scenario_txs)
        return np.asarray([list(values.values())], dtype=np.float32)

    def explain_features(self, scenario_txs: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """Return actual XGBoost prediction contributions for the binary model."""
        if not self.is_loaded:
            self.load_model()
        features = self._feature_dict(scenario_txs)
        matrix = np.asarray([list(features.values())], dtype=np.float32)
        import xgboost as xgb

        contributions = self.model.get_booster().predict(
            xgb.DMatrix(matrix), pred_contribs=True
        )
        values = np.asarray(contributions[0], dtype=float)
        if len(values) != len(self.feature_names) + 1:
            raise RuntimeError(
                f"Unexpected contribution vector length {len(values)} for {len(self.feature_names)} features"
            )
        ranked = sorted(
            zip(self.feature_names, matrix[0], values[:-1]),
            key=lambda item: abs(float(item[2])),
            reverse=True,
        )[:top_n]
        return [
            {
                "feature_name": name,
                "value": float(value),
                "shap_value": float(contribution),
                "direction": "RISK_INCREASING" if contribution >= 0 else "RISK_DECREASING",
            }
            for name, value, contribution in ranked
        ]

    def _decode_typology(self, class_index: int) -> str:
        if not self.typology_classes:
            raise RuntimeError("Typology classes are not loaded")
        if class_index < 0 or class_index >= len(self.typology_classes):
            raise RuntimeError(f"Typology class index out of range: {class_index}")
        return self.typology_classes[class_index]

    def predict_risk(self, target: Any) -> Dict[str, Any]:
        """Predict binary risk and, when illicit, decode the typology safely."""
        if not self.is_loaded:
            self.load_model()

        from backend.app.services.data_service import data_service

        tx_records: List[Dict[str, Any]] = []
        scenario_id = None
        if isinstance(target, (int, str)):
            lookup = target
            if isinstance(target, str):
                try:
                    lookup = int(target)
                except ValueError:
                    pass
            tx_record = data_service.txid_map.get(lookup)
            if not tx_record:
                return {
                    "risk_score": 0.0,
                    "is_illicit": False,
                    "confidence": 0.0,
                    "model_used": "unknown",
                    "scenario_id": None,
                    "typology": "normal",
                }
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

        if not tx_records:
            return {
                "risk_score": 0.0,
                "is_illicit": False,
                "confidence": 0.0,
                "model_used": "unknown",
                "scenario_id": scenario_id,
                "typology": "normal",
            }

        try:
            features = self.extract_features(tx_records)
            score = float(self.model.predict_proba(features)[0][1])
        except Exception as exc:
            logger.exception("Binary V7 inference failed")
            return {
                "risk_score": 0.0,
                "is_illicit": False,
                "confidence": 0.0,
                "model_used": "binary_error",
                "scenario_id": scenario_id,
                "typology": "unknown",
                "error": str(exc),
            }

        is_illicit = bool(score >= 0.5)
        result: Dict[str, Any] = {
            "risk_score": round(score, 4),
            "is_illicit": is_illicit,
            "confidence": round(abs(score - 0.5) * 2, 4),
            "model_used": "xgboost_v7",
            "scenario_id": scenario_id,
            "typology": "normal" if not is_illicit else "unknown",
        }

        if is_illicit:
            try:
                class_index = int(self.typology_model.predict(features)[0])
                result["typology"] = self._decode_typology(class_index)
            except Exception as exc:
                # Typology failure must not erase a valid binary result.
                logger.exception("Typology V7 inference/decoding failed")
                result["typology"] = "unknown"
                result["typology_error"] = str(exc)

        return result


ml_service = MLService()
