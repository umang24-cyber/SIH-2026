"""
Isolation Forest Anomaly Detection Service.

Serves per-scenario Anomaly/Unusualness Scores (0–100) computed against a
model of normal (licit) behavior.  This is entirely separate from the
XGBoost binary/typology classifiers — scores must never be merged with
risk_score or typology_confidence.

Score semantics:
  0   = indistinguishable from licit training distribution
  100 = maximally anomalous relative to licit training distribution

Normalization formula (fitted on licit-only train set, stored in JSON):
  anomaly_score = clip((raw_max - score_samples(x)) /
                       (raw_max - raw_min) * 100, 0, 100)

IMPORTANT:
- This score is NOT a probability.
- This score is NOT combined with risk_score anywhere in the codebase.
- The label "Anomaly/Unusualness Score" must be used consistently.
"""
import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.app.core.config import BASE_DIR

logger = logging.getLogger(__name__)

ML_MODELS_DIR = BASE_DIR / "ml" / "models"
MODEL_PATH_V8 = ML_MODELS_DIR / "anomaly_model_v8.pkl"
MODEL_PATH_V7 = ML_MODELS_DIR / "anomaly_model_v7.pkl"
MODEL_PATH = MODEL_PATH_V8 if MODEL_PATH_V8.exists() else MODEL_PATH_V7
PARAMS_PATH = ML_MODELS_DIR / "anomaly_norm_params.json"

# Threshold above which a scenario is reported as "HIGH" anomaly
_HIGH_ANOMALY_THRESHOLD = 70.0


class AnomalyService:
    def __init__(self):
        self._model = None
        self._raw_min: float = 0.0
        self._raw_max: float = 0.0
        self._feature_names: List[str] = []
        self.is_loaded: bool = False

    def load_model(self):
        """Load the fitted IsolationForest and normalization parameters."""
        if self.is_loaded:
            return
        if not MODEL_PATH.exists():
            raise RuntimeError(
                f"Anomaly model not found: {MODEL_PATH}. "
                "Run ml/05_anomaly_detection.py first."
            )
        if not PARAMS_PATH.exists():
            raise RuntimeError(f"Anomaly normalization params not found: {PARAMS_PATH}.")

        with open(MODEL_PATH, "rb") as f:
            self._model = pickle.load(f)

        with open(PARAMS_PATH) as f:
            params = json.load(f)

        self._raw_min       = float(params["raw_train_min"])
        self._raw_max       = float(params["raw_train_max"])
        self._feature_names = params["feature_names"]
        self.is_loaded      = True

        logger.info(
            "AnomalyService loaded: n_estimators=%d, "
            "norm_range=[%.4f, %.4f], features=%d",
            self._model.n_estimators,
            self._raw_min, self._raw_max,
            len(self._feature_names),
        )

    def _normalize(self, raw_scores: np.ndarray) -> np.ndarray:
        """
        Convert raw score_samples() output to 0–100 Anomaly/Unusualness Score.
        Higher = more anomalous.  Clamped to [0, 100].
        """
        span = self._raw_max - self._raw_min
        if span == 0:
            return np.zeros_like(raw_scores)
        return np.clip((self._raw_max - raw_scores) / span * 100.0, 0.0, 100.0)

    def score_scenario_from_features(
        self, feature_dict: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Score a single scenario given its pre-computed feature dict.
        Returns anomaly_score_0_100 and supporting metadata.
        Used by anomaly_service.score_scenario() after the ML serving
        feature extraction path.
        """
        if not self.is_loaded:
            self.load_model()

        missing = [f for f in self._feature_names if f not in feature_dict]
        if missing:
            raise ValueError(f"Feature dict is missing anomaly model features: {missing}")

        x = np.array(
            [[float(feature_dict[f]) for f in self._feature_names]],
            dtype=np.float32,
        )
        raw = self._model.score_samples(x)
        score = float(self._normalize(raw)[0])
        is_high = score >= _HIGH_ANOMALY_THRESHOLD

        return {
            "anomaly_score": round(score, 2),
            "anomaly_label": "HIGH" if is_high else ("MEDIUM" if score >= 40.0 else "LOW"),
            "anomaly_raw_if_score": round(float(raw[0]), 6),
            "anomaly_high_threshold": _HIGH_ANOMALY_THRESHOLD,
            "anomaly_interpretation": (
                "Anomaly/Unusualness Score — measures how unlike normal (licit) "
                "Bitcoin activity this scenario's behavior pattern is. "
                "NOT a probability. NOT combined with ML risk score."
            ),
        }

    def score_scenario(
        self,
        scenario_txs: List[Dict[str, Any]],
        scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Score a scenario given its raw transaction records.
        Extracts features using the SAME ml_service feature path, then scores.
        """
        if not self.is_loaded:
            self.load_model()

        # Import ml_service only here to avoid circular imports
        from backend.app.services.ml_service import ml_service

        if not ml_service.is_loaded:
            ml_service.load_model()

        feature_dict = ml_service._feature_dict(scenario_txs, scenario_id=scenario_id)
        return self.score_scenario_from_features(feature_dict)

    def score_scenario_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Score a scenario by its ID by looking up its transactions from data_service.
        Returns None if the scenario is not found.
        """
        if not self.is_loaded:
            self.load_model()

        from backend.app.services.data_service import data_service

        if not data_service.is_ready:
            data_service.initialize()

        txids = data_service.scenario_tx_map.get(scenario_id)
        if not txids:
            return None

        tx_records = [
            data_service.txid_map[tid]
            for tid in txids
            if tid in data_service.txid_map
        ]
        if not tx_records:
            return None

        try:
            result = self.score_scenario(tx_records, scenario_id=scenario_id)
            result["scenario_id"] = scenario_id
            return result
        except Exception:
            logger.exception("Anomaly scoring failed for scenario %s", scenario_id)
            return None


# Global singleton
anomaly_service = AnomalyService()
