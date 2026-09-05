"""Focused regression tests for the V7 integration fixes."""

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]


def test_feature_module_imports_have_no_pipeline_side_effects():
    tracked_artifacts = [
        ROOT / "data/processed/scenario_features_train.csv",
        ROOT / "data/processed/scenario_features_test.csv",
        ROOT / "data/processed/scenario_graph_features_train.csv",
        ROOT / "data/processed/scenario_graph_features_test.csv",
    ]
    before = {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in tracked_artifacts}
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import importlib; importlib.import_module('ml.02_feature_engineering'); importlib.import_module('ml.02b_graph_features')",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    after = {path: (path.stat().st_mtime_ns, path.stat().st_size) for path in tracked_artifacts}
    assert before == after
    assert "LOADING & PROCESSING" not in result.stdout
    assert "Processing graph features" not in result.stdout


@pytest.fixture(scope="module")
def loaded_service():
    from backend.app.services.data_service import data_service
    from backend.app.services.ml_service import MLService

    if not data_service.is_ready:
        data_service.initialize()
    service = MLService()
    service.load_model()
    return service, data_service


def test_typology_class_index_decoding(loaded_service):
    service, _ = loaded_service
    assert service.typology_classes == ["layering", "mixing", "peeling_chain", "ransomware"]
    assert [service._decode_typology(i) for i in range(4)] == service.typology_classes


def test_known_licit_and_illicit_scenarios(loaded_service):
    service, data_service = loaded_service
    licit_scenario = next(s for s in sorted(data_service.scenario_tx_map) if s.startswith("normal_"))
    illicit_scenario = next(s for s in sorted(data_service.scenario_tx_map) if s.startswith("layering_"))

    licit_result = service.predict_risk(data_service.scenario_tx_map[licit_scenario][0])
    illicit_result = service.predict_risk(data_service.scenario_tx_map[illicit_scenario][0])

    assert licit_result["is_illicit"] is False
    assert illicit_result["is_illicit"] is True
    assert illicit_result["typology"] in service.typology_classes


def test_typology_failure_preserves_binary_result():
    from backend.app.services.ml_service import MLService

    class BinaryModel:
        def predict_proba(self, _features):
            return np.array([[0.05, 0.95]])

    class FailingTypologyModel:
        def predict(self, _features):
            raise RuntimeError("synthetic typology failure")

    service = MLService()
    service.is_loaded = True
    service.feature_names = ["feature"]
    service.model = BinaryModel()
    service.typology_model = FailingTypologyModel()
    service.extract_features = lambda _records: np.zeros((1, 1), dtype=np.float32)

    result = service.predict_risk([{}])

    assert result["is_illicit"] is True
    assert result["risk_score"] == 0.95
    assert result["typology"] == "unknown"
    assert "typology_error" in result
