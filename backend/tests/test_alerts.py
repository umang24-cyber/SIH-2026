import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.typology_detector import TypologyDetector
from backend.app.models.schemas import AlertSummary

@pytest.fixture
def mock_services():
    with patch("backend.app.services.typology_detector.data_service") as mock_data, \
         patch("backend.app.services.ml_service.ml_service") as mock_ml, \
         patch("backend.app.services.anomaly_service.anomaly_service") as mock_anomaly:
        
        mock_data.is_ready = True
        mock_ml.is_loaded = True
        mock_anomaly.is_loaded = True
        yield mock_data, mock_ml, mock_anomaly


def create_mock_tx(txid, addresses):
    return {
        "txid": txid,
        "timestamp": "2024-01-01T00:00:00Z",
        "input_addresses": addresses,
        "output_addresses": addresses,
        "input_amounts": [1.0],
        "output_amounts": [1.0],
        "fee_btc": 0.0001,
        "script_type": "P2PKH"
    }

def test_ranking_by_risk_score(mock_services):
    """TEST 1: Three scenarios sorted by risk_score DESC"""
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_A": [1], "sc_B": [2], "sc_C": [3]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"]), 2: create_mock_tx(2, ["w2"]), 3: create_mock_tx(3, ["w3"])}

    def mock_score_candidate(txs, candidate_id):
        sc_id = candidate_id.replace("alert_", "")
        scores = {"sc_A": 0.99, "sc_B": 0.71, "sc_C": 0.54}
        return {"is_illicit": True, "risk_score": scores[sc_id], "binary_confidence": scores[sc_id], "typology_confidence": 0.8, "typology": "mixing"}
    mock_ml.score_candidate.side_effect = mock_score_candidate
    mock_anomaly.score_scenario_id.return_value = {"anomaly_score": 0.0, "anomaly_label": "LOW"}

    detector = TypologyDetector()
    detector.scan_all_typologies()
    alerts = detector.get_alerts(sort_by="risk_score")
    assert [a.scenario_id for a in alerts] == ["sc_A", "sc_B", "sc_C"]

def test_ranking_risk_over_anomaly(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_A": [1], "sc_B": [2]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"]), 2: create_mock_tx(2, ["w2"])}

    def mock_score_candidate(txs, candidate_id):
        sc_id = candidate_id.replace("alert_", "")
        scores = {"sc_A": 0.95, "sc_B": 0.90}
        return {"is_illicit": True, "risk_score": scores[sc_id], "binary_confidence": scores[sc_id], "typology_confidence": 0.8, "typology": "ransomware"}
    mock_ml.score_candidate.side_effect = mock_score_candidate

    def mock_anomaly_score(sc_id):
        return {"anomaly_score": 20.0 if sc_id == "sc_A" else 100.0, "anomaly_label": "HIGH"}
    mock_anomaly.score_scenario_id.side_effect = mock_anomaly_score

    detector = TypologyDetector()
    detector.scan_all_typologies()
    alerts = detector.get_alerts(sort_by="risk_score")
    assert [a.scenario_id for a in alerts] == ["sc_A", "sc_B"]

def test_ranking_risk_over_typology_confidence(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_A": [1], "sc_B": [2]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"]), 2: create_mock_tx(2, ["w2"])}

    def mock_score_candidate(txs, candidate_id):
        sc_id = candidate_id.replace("alert_", "")
        return {"is_illicit": True, "risk_score": 0.95 if sc_id == "sc_A" else 0.90, "binary_confidence": 0.95 if sc_id == "sc_A" else 0.90, "typology_confidence": 0.60 if sc_id == "sc_A" else 0.99, "typology": "mixing"}
    
    mock_ml.score_candidate.side_effect = mock_score_candidate
    mock_anomaly.score_scenario_id.return_value = {"anomaly_score": 0.0, "anomaly_label": "LOW"}

    detector = TypologyDetector()
    detector.scan_all_typologies()
    alerts = detector.get_alerts(sort_by="risk_score")
    assert [a.scenario_id for a in alerts] == ["sc_A", "sc_B"]

def test_normal_parent_fragment_isolation(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_normal": [1]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"])}
    mock_ml.score_candidate.return_value = {"is_illicit": False, "risk_score": 0.20, "binary_confidence": 0.20, "typology_confidence": 0.1, "typology": "normal"}
    mock_anomaly.score_scenario_id.return_value = {"anomaly_score": 0.0, "anomaly_label": "LOW"}
    
    detector = TypologyDetector()
    with patch.object(detector, "_discover_peeling_chain_candidates") as mock_peel:
        mock_peel.return_value = [{"scenario_id": "sc_normal", "candidate_id": "fake_1"}]
        detector.scan_all_typologies()
        alerts = detector.get_alerts()
        assert len(alerts) == 0

def test_deduplication_and_evidence_attachment(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_illicit": [1, 2, 3]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"]), 2: create_mock_tx(2, ["w2"]), 3: create_mock_tx(3, ["w3"])}
    mock_ml.score_candidate.return_value = {"is_illicit": True, "risk_score": 0.90, "binary_confidence": 0.90, "typology_confidence": 0.90, "typology": "ransomware"}
    mock_anomaly.score_scenario_id.return_value = {"anomaly_score": 0.0, "anomaly_label": "LOW"}

    detector = TypologyDetector()
    with patch.object(detector, "_discover_peeling_chain_candidates") as mock_peel, \
         patch.object(detector, "_discover_layering_candidates") as mock_layer, \
         patch.object(detector, "_discover_mixing_candidates") as mock_mix, \
         patch.object(detector, "_discover_ransomware_candidates") as mock_rans:
        
        mock_peel.return_value = [{"scenario_id": "sc_illicit", "candidate_id": "ev_1"}]
        mock_layer.return_value = [{"scenario_id": "sc_illicit", "candidate_id": "ev_2"}]
        mock_mix.return_value = [{"scenario_id": "sc_illicit", "candidate_id": "ev_3"}]
        mock_rans.return_value = []
        
        detector.scan_all_typologies()
        alerts = detector.get_alerts()
        assert len(alerts) == 1
        assert len(alerts[0].evidence) == 3

def test_high_anomaly_normal_risk_no_alert(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_normal": [1]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"])}
    mock_ml.score_candidate.return_value = {"is_illicit": False, "risk_score": 0.20, "binary_confidence": 0.20, "typology_confidence": 0.1, "typology": "normal"}
    mock_anomaly.score_scenario_id.return_value = {"anomaly_score": 99.0, "anomaly_label": "HIGH"}
    
    detector = TypologyDetector()
    detector.scan_all_typologies()
    alerts = detector.get_alerts()
    assert len(alerts) == 0

def test_deterministic_tie_break(mock_services):
    mock_data, mock_ml, mock_anomaly = mock_services
    mock_data.scenario_tx_map = {"sc_A": [1], "sc_B": [2]}
    mock_data.txid_map = {1: create_mock_tx(1, ["w1"]), 2: create_mock_tx(2, ["w2"])}
    mock_ml.score_candidate.return_value = {"is_illicit": True, "risk_score": 0.85, "binary_confidence": 0.85, "typology_confidence": 0.80, "typology": "ransomware"}

    def mock_anomaly_score(sc_id):
        if sc_id == "sc_B": return {"anomaly_score": 50.0, "anomaly_label": "MEDIUM"}
        return {"anomaly_score": 10.0, "anomaly_label": "LOW"}
    mock_anomaly.score_scenario_id.side_effect = mock_anomaly_score

    detector = TypologyDetector()
    detector.scan_all_typologies()
    alerts = detector.get_alerts(sort_by="risk_score")
    assert len(alerts) == 2
    assert alerts[0].scenario_id == "sc_B"
    assert alerts[1].scenario_id == "sc_A"
