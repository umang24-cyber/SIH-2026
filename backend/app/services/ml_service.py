"""
ML model loading, V7 feature extraction, inference, and explanations.

The persisted V7 manifest is the single source of truth for model paths and
feature order. This module imports feature modules only for reusable functions;
their CLI pipelines are guarded and never run here.

Explainability covers BOTH models:
  - explain_binary_features(): binary is_illicit model (XGBoost SHAP contribs)
  - explain_typology_features(): typology multiclass model (TreeExplainer per-class)
"""

import importlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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
MANIFEST_V8 = BASE_DIR / "ml" / "manifests" / "MANIFEST_v8.json"
MANIFEST_V7 = BASE_DIR / "ml" / "manifests" / "MANIFEST_v7_candidate.json"
MANIFEST_PATH = MANIFEST_V8 if MANIFEST_V8.exists() else MANIFEST_V7

ENCODER_PATH_V8 = BASE_DIR / "data" / "processed_v8" / "script_type_encoder.json"
ENCODER_PATH_V7 = BASE_DIR / "data" / "processed" / "script_type_encoder.json"
ENCODER_PATH = ENCODER_PATH_V8 if ENCODER_PATH_V8.exists() else ENCODER_PATH_V7
TYPOLOGY_ENCODER_PATH = ML_DIR_MODELS / "typology_label_encoder.json"
FORBIDDEN_FEATURES = {
    "is_illicit",
    "pattern_type",
    "split",
    "scenario_id",
    "is_licit_exchange",
}
BINARY_ILLICIT_THRESHOLD = 0.50
TYPOLOGY_CONFIDENCE_THRESHOLD = 0.60

# Natural-language templates for typology SHAP explanations.
# Keyed by typology class name → list of (feature_name, direction, phrase) triples.
# If the actual top SHAP features for a prediction match an entry, the phrase is used;
# otherwise a generic fallback is constructed from raw feature names.
_TYPOLOGY_FEATURE_PHRASES: Dict[str, Dict[str, str]] = {
    "peeling_chain": {
        "max_chain_length": "long sequential hop chain",
        "amount_decay_slope": "declining output amounts across hops",
        "address_reuse_ratio": "high carry-address reuse",
        "change_output_ratio": "frequent 1-to-2 change outputs",
        "io_count_ratio": "low input-to-output ratio",
        "mean_num_outputs": "predominantly 1–2 outputs per hop",
        "graph_density": "sparse linear graph topology",
    },
    "layering": {
        "max_in_degree": "high fan-in degree at consolidation node",
        "max_out_degree": "high fan-out degree at dispersion node",
        "avg_clustering": "clustering from co-participation",
        "unique_output_addrs": "large number of unique output addresses",
        "mean_num_outputs": "high output arity per transaction",
        "degree_assortativity": "assortative mixing between high-degree nodes",
    },
    "mixing": {
        "output_amount_gini": "near-equal output denomination (low Gini)",
        "denomination_entropy": "low denomination entropy",
        "io_count_ratio": "balanced N-to-N input/output count",
        "unique_input_addrs": "many distinct co-spending parties",
        "round_number_ratio": "high round-number output amounts",
        "avg_clustering": "multi-party co-spending clustering",
    },
    "ransomware": {
        "suspicious_infra_ratio": "high proportion of suspicious relay infrastructure",
        "num_txns": "short concentrated payment burst",
        "burstiness_B": "high inter-transaction burstiness",
        "inter_tx_delta_min": "extremely short inter-transaction gaps",
        "unique_asn_count": "concentrated relay ASN origin",
        "prop_delta_mean": "anomalous propagation delay from high-risk relay",
        "unique_ip_count": "few relay IPs (concentrated origin)",
    },
}

# Plain-language names for binary-model SHAP output.  Unknown features still
# use the same readable raw-name fallback used by the typology explanation.
_BINARY_FEATURE_PHRASES: Dict[str, str] = {
    "num_txns": "transaction count",
    "suspicious_infra_ratio": "suspicious relay infrastructure",
    "prop_delta_cv": "propagation-delay variability",
    "output_amount_gini": "output amount inequality",
    "fee_ratio_std": "fee-ratio variation",
}


def _make_typology_explanation(
    typology: str,
    confidence: float,
    top_shap: List[Dict[str, Any]],
) -> str:
    """
    Generate a human-readable typology explanation from actual top SHAP features.
    Uses phrase templates where available, raw feature names as fallback.
    """
    phrases = _TYPOLOGY_FEATURE_PHRASES.get(typology, {})
    evidence_parts = []
    for item in top_shap[:3]:
        fname = item["feature_name"]
        direction = item["direction"]
        phrase = phrases.get(fname)
        if phrase:
            qualifier = "elevated" if direction == "RISK_INCREASING" else "reduced"
            evidence_parts.append(f"{qualifier} {phrase}")
        else:
            qualifier = "↑" if direction == "RISK_INCREASING" else "↓"
            evidence_parts.append(f"{qualifier}{fname}={item['value']:.3g}")

    evidence_str = "; ".join(evidence_parts) if evidence_parts else "feature pattern match"
    return (
        f"Flagged as likely {typology} (confidence {confidence*100:.1f}%): "
        f"{evidence_str}."
    )


def _make_generic_illicit_explanation(
    binary_confidence: float,
    binary_shap: List[Dict[str, Any]],
) -> str:
    """Explain an illicit prediction when no typology clears the confidence gate."""
    evidence_parts = []
    for item in binary_shap[:3]:
        fname = item["feature_name"]
        direction = item["direction"]
        phrase = _BINARY_FEATURE_PHRASES.get(fname, fname.replace("_", " "))
        qualifier = "elevated" if direction == "RISK_INCREASING" else "reduced"
        evidence_parts.append(
            f"{qualifier} {phrase} ({fname}={item['value']:.3g}, "
            f"SHAP {item['shap_value']:+.3f})"
        )

    evidence_str = "; ".join(evidence_parts) if evidence_parts else "no available feature attributions"
    return (
        f"Flagged as illicit by the binary model (confidence {binary_confidence*100:.1f}%): "
        f"{evidence_str}. Typology is ambiguous below the "
        f"{TYPOLOGY_CONFIDENCE_THRESHOLD:.0%} confidence threshold."
    )


class MLService:
    def __init__(self):
        self.model = None
        self.typology_model = None
        self.is_loaded = False
        self.feature_names: List[str] = []
        self.script_type_encoder: Dict[str, int] = {}
        self.typology_classes: List[str] = []
        self._scenario_feature_cache: Dict[str, Dict[str, float]] = {}

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

    def _feature_dict(self, scenario_txs: List[Dict[str, Any]], scenario_id: Optional[str] = None) -> Dict[str, float]:
        """
        Compute features from raw transaction records using the EXACT same
        compute_scenario_features + compute_graph_features functions used at
        training time. This guarantees zero train/serve skew.
        Caches the feature vector by scenario_id if provided.
        """
        if not scenario_txs:
            raise ValueError("At least one transaction is required for feature extraction")

        if scenario_id is not None and scenario_id in self._scenario_feature_cache:
            return self._scenario_feature_cache[scenario_id]

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
        
        result = {name: float(merged[name]) for name in self.feature_names}
        if scenario_id is not None:
            self._scenario_feature_cache[scenario_id] = result
        return result

    def extract_features(self, scenario_txs: List[Dict[str, Any]], scenario_id: Optional[str] = None) -> np.ndarray:
        """Extract a V7 feature matrix in canonical manifest order."""
        values = self._feature_dict(scenario_txs, scenario_id=scenario_id)
        return np.asarray([list(values.values())], dtype=np.float32)

    def explain_binary_features(self, scenario_txs: List[Dict[str, Any]], top_n: int = 5, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Return XGBoost prediction contributions (SHAP) for the BINARY is_illicit model.
        Uses the native XGBoost pred_contribs which is TreeSHAP-equivalent.
        """
        if not self.is_loaded:
            self.load_model()
        features = self._feature_dict(scenario_txs, scenario_id=scenario_id)
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

    # Kept for backwards compatibility – delegates to the renamed method.
    def explain_features(self, scenario_txs: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        return self.explain_binary_features(scenario_txs, top_n=top_n)

    def explain_typology_features(
        self,
        scenario_txs: List[Dict[str, Any]],
        predicted_class_index: int,
        top_n: int = 5,
        scenario_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return XGBoost SHAP contributions for the TYPOLOGY multiclass model,
        specific to the predicted class (the class the model assigned).

        XGBoost's pred_contribs for multi:softprob returns a matrix of shape
        (1, n_classes * (n_features + 1)) where contributions for class k occupy
        columns [k*(n_features+1) : (k+1)*(n_features+1)].
        """
        if not self.is_loaded:
            self.load_model()
        features = self._feature_dict(scenario_txs, scenario_id=scenario_id)
        matrix = np.asarray([list(features.values())], dtype=np.float32)
        import xgboost as xgb

        # pred_contribs=True on a multiclass booster returns shape
        # (n_samples, n_classes, n_features+1)
        contributions = self.typology_model.get_booster().predict(
            xgb.DMatrix(matrix), pred_contribs=True
        )
        # contributions shape: (1, n_classes, n_features+1)
        contribs_flat = np.asarray(contributions)
        if contribs_flat.ndim == 3:
            # Expected: (1, n_classes, n_features+1)
            class_contribs = contribs_flat[0, predicted_class_index, :-1]
        elif contribs_flat.ndim == 2:
            # Some XGBoost versions flatten: (1, n_classes*(n_features+1))
            n_feats = len(self.feature_names)
            start = predicted_class_index * (n_feats + 1)
            class_contribs = contribs_flat[0, start : start + n_feats]
        else:
            raise RuntimeError(f"Unexpected SHAP contributions shape: {contribs_flat.shape}")

        ranked = sorted(
            zip(self.feature_names, matrix[0], class_contribs),
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
        """
        Predict binary risk and, when illicit, decode the typology safely.
        Returns calibrated probabilities for both binary and typology models.
        ``binary_confidence`` and ``typology_confidence`` are always separate.
        """
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
                    "binary_confidence": 0.0,
                    "model_used": "unknown",
                    "scenario_id": None,
                    "typology": "normal",
                    "typology_confidence": 0.0,
                    "typology_class_index": -1,
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
                "binary_confidence": 0.0,
                "model_used": "unknown",
                "scenario_id": scenario_id,
                "typology": "normal",
                "typology_confidence": 0.0,
                "typology_class_index": -1,
            }

        try:
            features = self.extract_features(tx_records, scenario_id=scenario_id)
            score = float(self.model.predict_proba(features)[0][1])
        except Exception as exc:
            logger.exception("Binary V7 inference failed")
            return {
                "risk_score": 0.0,
                "is_illicit": False,
                "binary_confidence": 0.0,
                "model_used": "binary_error",
                "scenario_id": scenario_id,
                "typology": "unknown",
                "typology_confidence": 0.0,
                "typology_class_index": -1,
                "error": str(exc),
            }

        is_illicit = bool(score >= BINARY_ILLICIT_THRESHOLD)
        result: Dict[str, Any] = {
            "risk_score": round(score, 4),
            "is_illicit": is_illicit,
            # Canonical meaning: binary XGBoost P(illicit). risk_score is
            # intentionally the same quantity; it is not a second formula.
            "binary_confidence": round(score, 4),
            "model_used": "xgboost_v7",
            "scenario_id": scenario_id,
            "typology": "normal" if not is_illicit else "unknown",
            "typology_confidence": 0.0,
            "typology_class_index": -1,
        }

        if is_illicit:
            try:
                typ_proba = self.typology_model.predict_proba(features)[0]
                class_index = int(np.argmax(typ_proba))
                typ_confidence = float(typ_proba[class_index])
                result["typology"] = self._decode_typology(class_index)
                result["typology_confidence"] = round(typ_confidence, 4)
                result["typology_class_index"] = class_index
            except Exception as exc:
                # Typology failure must not erase a valid binary result.
                logger.exception("Typology V7 inference/decoding failed")
                result["typology"] = "unknown"
                result["typology_error"] = str(exc)

        return result

    def score_candidate(
        self,
        scenario_txs: List[Dict[str, Any]],
        candidate_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full ML scoring for a candidate subgraph (list of tx dicts).
        Returns binary risk + separate binary/typology confidence fields + SHAP explanations
        for BOTH models.  Used by typology_detector to produce ML-driven alerts.
        """
        if not self.is_loaded:
            self.load_model()

        # candidate_id format is "alert_{sc_id}"
        scenario_id = candidate_id.replace("alert_", "") if candidate_id and candidate_id.startswith("alert_") else None

        import time
        t_start = time.perf_counter()
        
        try:
            features = self.extract_features(scenario_txs, scenario_id=scenario_id)
            t_features = time.perf_counter()
            bin_proba = self.model.predict_proba(features)[0]
            risk_score = float(bin_proba[1])
            is_illicit = bool(risk_score >= BINARY_ILLICIT_THRESHOLD)
            t_binary = time.perf_counter()
        except Exception as exc:
            logger.exception("Binary inference failed for candidate %s", candidate_id)
            return {
                "risk_score": 0.0, "is_illicit": False, "binary_confidence": 0.0, "typology_confidence": 0.0,
                "typology": "unknown", "typology_class_index": -1, "binary_shap": [], "typology_shap": [],
                "typology_explanation": "ML inference failed.", "error": str(exc), "profiling": {}
            }

        typology = "normal"
        typ_confidence = 0.0
        typ_class_idx = -1
        typ_shap: List[Dict[str, Any]] = []
        typ_explanation = ""

        if is_illicit:
            try:
                typ_proba = self.typology_model.predict_proba(features)[0]
                typ_class_idx = int(np.argmax(typ_proba))
                typ_confidence = float(typ_proba[typ_class_idx])
                if typ_confidence >= TYPOLOGY_CONFIDENCE_THRESHOLD:
                    typology = self._decode_typology(typ_class_idx)
                    typ_shap = self.explain_typology_features(scenario_txs, predicted_class_index=typ_class_idx, top_n=5, scenario_id=scenario_id)
                    typ_explanation = _make_typology_explanation(typology, typ_confidence, typ_shap)
                else:
                    ranked_classes = np.argsort(typ_proba)[::-1][:2]
                    first_idx, second_idx = (int(index) for index in ranked_classes)
                    first_name = self._decode_typology(first_idx)
                    second_name = self._decode_typology(second_idx)
                    typology = f"ambiguous between {first_name} ({typ_proba[first_idx]*100:.1f}%) and {second_name} ({typ_proba[second_idx]*100:.1f}%)"
            except Exception as exc:
                logger.exception("Typology inference/SHAP failed for candidate %s", candidate_id)
                typ_explanation = "Typology scoring failed."

        t_typology = time.perf_counter()
        
        # Binary SHAP
        bin_shap: List[Dict[str, Any]] = []
        try:
            bin_shap = self.explain_binary_features(scenario_txs, top_n=5, scenario_id=scenario_id)
        except Exception:
            logger.exception("Binary SHAP failed for candidate %s", candidate_id)

        binary_confidence = round(risk_score, 4)
        if is_illicit and typ_confidence < TYPOLOGY_CONFIDENCE_THRESHOLD:
            typ_explanation = _make_generic_illicit_explanation(binary_confidence, bin_shap)

        t_end = time.perf_counter()
        profiling = {
            "feature_time": t_features - t_start,
            "binary_time": t_binary - t_features,
            "typology_time": t_end - t_binary, # includes SHAP for both
        }

        return {
            "risk_score": round(risk_score, 4),
            "is_illicit": is_illicit,
            "binary_confidence": binary_confidence,
            "typology": typology,
            "typology_confidence": round(typ_confidence, 4),
            "typology_class_index": typ_class_idx,
            "binary_shap": bin_shap,
            "typology_shap": typ_shap,
            "typology_explanation": typ_explanation,
            "profiling": profiling,
        }


ml_service = MLService()
