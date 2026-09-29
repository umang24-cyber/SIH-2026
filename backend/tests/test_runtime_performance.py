"""Performance contracts: reuse exact inputs, not stale scores or partial scans."""
import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from backend.app.services.feature_cache import FeatureCache
from backend.app.services.ml_service import MLService
from backend.app.services.typology_detector import TypologyDetector
from backend.tests.test_alerts import mock_services, create_mock_tx


def test_content_cache_survives_restart_but_invalidates_changed_data_and_schema(tmp_path):
    path = tmp_path / "features.sqlite3"
    records = [{**create_mock_tx(1, ["wallet"]), "relay_timestamp": "2024-01-01T00:00:00Z"}]

    def service():
        ml = MLService()
        ml.feature_names = ["num_txns"]
        ml._feature_namespace = "test-version-1"
        ml.feature_cache = FeatureCache(path)
        return ml

    with patch("backend.app.services.ml_service.compute_scenario_features", return_value={"num_txns": 1}) as compute, \
         patch("backend.app.services.ml_service.compute_graph_features", return_value={}):
        first = service()
        assert first._feature_dict(records, "same-name") == {"num_txns": 1.0}
        first.feature_cache.close()
        second = service()
        assert second._feature_dict(records, "same-name") == {"num_txns": 1.0}
        assert compute.call_count == 1
        # Labels are not feature inputs and must not enter the feature key.
        assert second._feature_dict([{**records[0], "is_illicit": 1}], "same-name") == {"num_txns": 1.0}
        assert compute.call_count == 1
        second._feature_dict([{**records[0], "fee_btc": 0.123}], "same-name")
        assert compute.call_count == 2
        second._feature_namespace = "changed-pipeline"
        second._feature_dict(records, "same-name")
        assert compute.call_count == 3
        second.feature_cache.close()


def test_corrupt_or_wrong_shape_feature_cache_is_a_miss(tmp_path):
    cache = FeatureCache(tmp_path / "features.sqlite3")
    cache.put("key", [1.0])
    cache.flush()
    assert cache.get("key", ["x"]) == {"x": 1.0}
    assert cache.get("key", ["x", "y"]) is None
    with sqlite3.connect(cache.path) as conn:
        conn.execute("UPDATE features SET values_json = ?", ('[NaN]',))
    assert cache.get("key", ["x"]) is None
    with sqlite3.connect(cache.path) as conn:
        conn.execute("UPDATE features SET values_json = ?", ('{"not": "a vector"}',))
    assert cache.get("key", ["x"]) is None
    cache.close()


def test_unreadable_sqlite_cache_falls_back_without_reopening_per_scenario(tmp_path):
    path = tmp_path / "invalid.sqlite3"
    path.write_bytes(b"not a SQLite database")
    cache = FeatureCache(path)
    assert cache.get("key", ["x"]) is None
    assert cache._disk_disabled
    cache.put("key", [1.0])
    assert cache.get("key", ["x"]) is None
    cache.close()


def test_alert_queue_batches_all_scenarios_but_only_explains_visible_alerts(mock_services):
    data, ml, anomaly = mock_services
    data.scenario_tx_map = {f"scenario_{i}": [i] for i in range(5)}
    data.txid_map = {i: create_mock_tx(i, [f"w{i}"]) for i in range(5)}
    ml.score_scenarios.side_effect = None
    ml.score_scenarios.return_value = {
        name: dict(is_illicit=True, risk_score=.8, binary_confidence=.8, typology_confidence=.9,
                   typology="mixing", _features={"num_txns": 1.0})
        for name in data.scenario_tx_map
    }
    anomaly.score_feature_batch.return_value = [{"anomaly_score": 0, "anomaly_label": "LOW"}] * 5
    ml.score_candidate.return_value = {"binary_shap": [], "typology_shap": [], "typology_explanation": "Actual explanation"}
    detector = TypologyDetector()
    assert len(detector.get_alerts(limit=2)) == 2
    assert ml.score_scenarios.call_count == 1
    assert anomaly.score_feature_batch.call_count == 1
    assert ml.score_candidate.call_count == 2
    assert len(detector.detected_alerts) == 5
    detector.get_alerts(limit=2)
    assert ml.score_candidate.call_count == 2
    detector.get_evidence("alert_scenario_4")
    assert ml.score_candidate.call_count == 3
    assert detector.scan_status["state"] == "complete"


def test_concurrent_alert_requests_share_one_scan_and_upload_revision_rescans(mock_services):
    data, ml, anomaly = mock_services
    data.scenario_tx_map = {"same": [1]}
    data.txid_map = {1: create_mock_tx(1, ["w"])}
    entered, release = threading.Event(), threading.Event()

    def score(scenarios, progress=None):
        entered.set()
        assert release.wait(5)
        return {"same": {"is_illicit": False}}

    ml.score_scenarios.side_effect = score
    detector = TypologyDetector()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(detector.get_alerts)
        assert entered.wait(5)
        second = pool.submit(detector.get_alerts)
        assert detector.scan_status["state"] == "running"
        release.set()
        assert first.result(timeout=5) == second.result(timeout=5) == []
    assert ml.score_scenarios.call_count == 1
    data.revision += 1
    detector.get_alerts()
    assert ml.score_scenarios.call_count == 2


def test_startup_tuple_conversion_preserves_runtime_values_without_helper_timestamps():
    from backend.app.services.data_service import DataService
    frame = pd.DataFrame([{"txid": 123, "timestamp": "2024-01-01", "input_addresses": ["a"],
                           "input_amounts": [1.25], "scenario_id": "case", "timestamp_dt": pd.Timestamp("2024-01-01") }])
    expected = [{k: v for k, v in row.items() if k != "timestamp_dt"} for row in frame.to_dict(orient="records")]
    service = DataService()
    with patch("backend.app.services.data_service.load_master_dataset", return_value=frame), \
         patch("backend.app.services.data_service.db_service.load_all_custom_transactions", return_value=[]):
        service.initialize()
    assert list(service.txid_map.values()) == expected
    assert service.scenario_tx_map["case"] == [123]
    assert service.address_in_map["a"] == [123]


def test_anomaly_batch_equals_single_model_scores():
    from sklearn.ensemble import IsolationForest
    from backend.app.services.anomaly_service import AnomalyService
    model = IsolationForest(n_estimators=8, random_state=42).fit(np.array([[0, 1], [1, 1], [2, 3], [3, 8]], dtype=np.float32))
    service = AnomalyService()
    service._model, service.is_loaded = model, True
    service._feature_names = ["a", "b"]
    service._raw_min, service._raw_max = -.8, -.2
    rows = [{"a": 0, "b": 1}, {"a": 5, "b": 7}]
    batch = service.score_feature_batch(rows)
    singles = [service.score_scenario_from_features(row) for row in rows]
    assert batch == [{key: row[key] for key in ("anomaly_score", "anomaly_label")} for row in singles]
