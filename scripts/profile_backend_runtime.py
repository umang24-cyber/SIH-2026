"""Measure real startup/full alert scan and optionally compare scores/features.

Run from the repository root with a temporary BITKAUN_DATA_DIR to measure cold
performance without mixing investigator data into the benchmark.
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    timings = {}
    start = time.perf_counter()
    from backend.app.main import app  # register the same components as real startup
    from backend.app.services.data_service import data_service
    from backend.app.services.db_service import db_service
    from backend.app.services.ml_service import ml_service
    from backend.app.services.anomaly_service import anomaly_service
    from backend.app.services.clustering_service import clustering_service
    from backend.app.services.typology_detector import typology_detector
    timings["imports_seconds"] = time.perf_counter() - start
    for name, action in [("database", db_service.ensure_initialized), ("data", data_service.initialize),
                         ("models", ml_service.load_model), ("anomaly_model", anomaly_service.load_model),
                         ("clustering", clustering_service.build_clusters)]:
        start = time.perf_counter()
        action()
        timings[name + "_seconds"] = time.perf_counter() - start
    start = time.perf_counter()
    first = typology_detector.get_alerts(limit=10)
    timings["first_alerts_seconds"] = time.perf_counter() - start
    start = time.perf_counter()
    typology_detector.get_alerts(limit=10)
    timings["repeated_alerts_seconds"] = time.perf_counter() - start
    results = {alert.scenario_id: [alert.risk_score, alert.binary_confidence,
               alert.typology_confidence, alert.predicted_pattern_type,
               alert.anomaly_score, alert.anomaly_label] for alert in typology_detector.detected_alerts}
    report = dict(timings=timings, transactions=len(data_service.txid_map),
                  alerts=len(results), first_page=[a.scenario_id for a in first], scores=results,
                  features=ml_service._scenario_feature_cache)
    if args.compare:
        import numpy as np
        previous = json.loads(args.compare.read_text(encoding="utf-8"))
        if previous["scores"] != results:
            mismatches = [key for key in set(previous["scores"]) | set(results)
                          if previous["scores"].get(key) != results.get(key)]
            raise AssertionError(f"Alert scoring differs for {len(mismatches)} scenarios: {mismatches[:10]}")
        if previous["first_page"] != report["first_page"]:
            raise AssertionError("Alert ordering differs")
        for scenario, values in previous["features"].items():
            for feature, value in values.items():
                np.testing.assert_allclose(report["features"][scenario][feature], value, rtol=1e-12, atol=1e-12,
                                           err_msg=f"{scenario}: {feature}")
        report["parity"] = "All alert scores/order exact; feature vectors within 1e-12 tolerance"
    args.output.write_text(json.dumps(report, allow_nan=False), encoding="utf-8")
    print(json.dumps({"timings": timings, "transactions": report["transactions"],
                      "alerts": report["alerts"], "parity": report.get("parity"),
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
