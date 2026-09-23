import sys
import logging

logging.basicConfig(level=logging.INFO)

from backend.app.services.data_service import data_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.ml_service import ml_service
from backend.app.services.anomaly_service import anomaly_service

def test_scan():
    print("Loading data...")
    data_service.initialize()
    ml_service.load_model()
    anomaly_service.load_model()
    print("Data loaded. Starting scan...")
    # we can limit max_candidates so it finishes quickly!
    typology_detector.scan_all_typologies(max_candidates=50)
    
    print(f"Scanned. Detected alerts: {len(typology_detector.detected_alerts)}")
    for a in typology_detector.detected_alerts[:3]:
        print(a.scenario_id, a.risk_score, a.anomaly_score, a.predicted_pattern_type)

if __name__ == "__main__":
    test_scan()
