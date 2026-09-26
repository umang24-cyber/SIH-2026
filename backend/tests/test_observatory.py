"""Focused Observatory API tests. Run: python -m unittest backend.tests.test_observatory."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes_observatory import router
from backend.app.services.observatory_service import DATA_DIR, MANIFEST, ROOT, ObservatoryService


class ObservatoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.service = ObservatoryService(self.root)
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.patcher = patch("backend.app.api.routes_observatory.observatory_service", self.service)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def artifact(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def manifest(self):
        return self.artifact(MANIFEST, json.loads((ROOT / MANIFEST).read_text(encoding="utf-8")))

    def reports(self):
        self.manifest()
        for name in ("binary", "typology"):
            path = f"ml/reports/{name}_metrics_v8.json"
            self.artifact(path, json.loads((ROOT / path).read_text(encoding="utf-8")))
        labels = self.root / DATA_DIR / "scenario_labels_test.csv"
        labels.parent.mkdir(parents=True, exist_ok=True)
        labels.write_bytes((ROOT / DATA_DIR / "scenario_labels_test.csv").read_bytes())

    def write_csv(self, name, rows):
        path = self.root / DATA_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def seed_dataset(self):
        def tx(txid, timestamp, scenario, illicit, amount, destination):
            return dict(txid=txid, timestamp=timestamp, scenario_id=scenario,
                        input_addresses='["shared"]', output_addresses=json.dumps([destination]),
                        output_amounts=json.dumps([amount]), script_type="P2PKH",
                        is_illicit=illicit, pattern_type="layering" if illicit else "normal")
        self.train = [tx(1, "2024-01-01 23:30:00", "train_a", 0, 1.25, "b"),
                      tx(2, "2024-01-03T02:30:00+02:00", "train_a", 0, 2.0, "b")]
        self.test = [tx(3, "2024-02-01T00:00:00Z", "test_b", 1, 0.5, "c")]
        self.write_csv("train_blockchain.csv", self.train)
        self.write_csv("test_blockchain.csv", self.test)
        self.write_csv("train_network.csv", [dict(txid=1, node_type="residential", country_code="IN"),
                                              dict(txid=2, node_type="", country_code="")])
        self.write_csv("test_network.csv", [dict(txid=3, node_type="datacenter", country_code="US")])

    def test_active_v8_metrics_match_saved_ml_report(self):
        self.reports()
        result = self.client.get("/api/observatory/performance")
        self.assertEqual(result.status_code, 200)
        payload = result.json()
        self.assertEqual(payload["status"], "available")
        self.assertEqual(payload["meta"]["model_version"], "v8")
        report = json.loads((ROOT / "ml/reports/binary_metrics_v8.json").read_text())
        binary = {m["id"]: m["value"] for m in payload["data"]["binary"]["metrics"]}
        self.assertEqual(binary["accuracy"], report["metrics"]["accuracy"])
        self.assertEqual(binary["precision"], report["metrics"]["precision"])
        self.assertEqual(binary["recall"], report["metrics"]["recall"])
        typ = json.loads((ROOT / "ml/reports/typology_metrics_v8.json").read_text())
        self.assertEqual({m["id"]: m["value"] for m in payload["data"]["typology"]["metrics"]}["macro_f1"], typ["macro_f1"])
        self.assertIsNone(payload["data"]["binary"]["confusion_matrix"])
        self.assertIsNone(payload["data"]["typology"]["confusion_matrix"])
        self.assertEqual(payload["data"]["typology"]["per_class"], [])
        self.assertEqual(payload["data"]["typology"]["sample_count"], 448)
        self.assertFalse(payload["data"]["curves_available"])

    def test_missing_corrupt_report_and_version_mismatch_fail_closed(self):
        self.assertEqual(self.service.performance().status, "unavailable")
        self.reports()
        path = self.root / "ml/reports/binary_metrics_v8.json"
        path.write_text("{invalid", encoding="utf-8")
        self.assertEqual(self.service.performance().status, "unavailable")
        self.reports()
        value = json.loads(path.read_text())
        value["metrics"]["precision"] = float("nan")
        self.artifact("ml/reports/binary_metrics_v8.json", value)
        self.assertEqual(self.service.performance().status, "unavailable")
        self.reports()
        manifest = json.loads((self.root / MANIFEST).read_text())
        manifest["typology_model"] = "typology_model_v9.ubj"
        self.artifact(MANIFEST, manifest)
        self.assertEqual(self.service.performance().status, "unavailable")

    def test_dataset_counts_utc_zero_buckets_and_isolation(self):
        self.seed_dataset()
        payload = self.client.get("/api/observatory/dataset?bucket=day").json()
        self.assertEqual(payload["status"], "available")
        data = payload["data"]
        self.assertEqual(data["totals"]["transactions"], 3)
        self.assertEqual(data["totals"]["scenarios"], 2)
        self.assertEqual(data["totals"]["unique_wallets"], 3)
        self.assertEqual(len(data["timeline"]), 32)
        self.assertEqual(data["timeline"][1]["transactions"], 0)
        self.assertEqual(data["timeline"][2]["transactions"], 1)
        self.assertAlmostEqual(sum(v["output_volume_btc"] for v in data["timeline"]), 3.75)
        self.assertEqual(sum(v["count"] for v in data["scenario_class_distribution"]), 2)
        self.assertEqual(sum(v["count"] for v in data["transaction_class_distribution"]), 3)
        self.assertEqual([v.transactions for v in self.service.dataset("month").data.timeline], [2, 1])
        (self.root / "investigator_case.json").write_text('{"transactions":999}', encoding="utf-8")
        self.assertEqual(self.service.dataset().data.totals.transactions, 3)

    def test_bad_join_and_duplicate_ids_fail_closed(self):
        self.seed_dataset()
        self.write_csv("test_network.csv", [dict(txid=999, node_type="tor", country_code="IN")])
        self.assertEqual(self.service.dataset().status, "unavailable")
        self.seed_dataset()
        self.test[0]["txid"] = 1
        self.write_csv("test_blockchain.csv", self.test)
        self.assertEqual(self.service.dataset().status, "unavailable")

    def test_cached_aggregates_invalidate_on_source_change(self):
        self.seed_dataset()
        with patch.object(self.service, "_rows", wraps=self.service._rows) as rows:
            before = self.service.dataset("month")
            self.service.dataset("week")
            self.assertEqual(rows.call_count, 4)
            self.test[0]["output_amounts"] = "[12.345]"
            self.write_csv("test_blockchain.csv", self.test)
            after = self.service.dataset("month")
            self.assertEqual(rows.call_count, 8)
        self.assertNotEqual(before.data.timeline[-1].output_volume_btc, after.data.timeline[-1].output_volume_btc)

    def test_gain_is_computed_from_active_model_and_not_a_saved_chart(self):
        import numpy as np
        import xgboost as xgb
        manifest = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
        manifest["feature_names"] = ["fee_ratio_mean", "graph_density", "prop_delta_mean"]
        manifest["feature_count"] = 3
        self.artifact(MANIFEST, manifest)
        model_path = self.root / "ml/models/binary_model_v8.ubj"
        model_path.parent.mkdir(parents=True)
        model = xgb.XGBClassifier(n_estimators=3, max_depth=1, min_child_weight=0, n_jobs=1)
        model.fit(np.array([[0, 1, 0], [0, 2, 0], [1, 1, 0], [1, 2, 0]]), np.array([0, 0, 1, 1]))
        model.save_model(model_path)
        response = self.client.get("/api/observatory/features?limit=1").json()
        self.assertEqual(response["status"], "available")
        self.assertEqual(response["data"]["method"], "normalized_xgboost_gain")
        self.assertEqual(response["data"]["features"][0]["id"], "fee_ratio_mean")
        self.assertAlmostEqual(sum(group["importance"] for group in response["data"]["groups"]), 1)
        self.assertEqual(len(response["data"]["features"]), 1)
        manifest["feature_names"] = ["is_illicit"]
        manifest["feature_count"] = 1
        self.artifact(MANIFEST, manifest)
        self.assertEqual(self.service.features().status, "unavailable")

    def test_diagrams_and_query_validation(self):
        pipeline = self.client.get("/api/observatory/pipeline").json()["data"]
        patterns = self.client.get("/api/observatory/patterns").json()["data"]["patterns"]
        self.assertEqual(len(patterns), 4)
        for diagram in [pipeline] + patterns:
            ids = {v["id"] for v in diagram["nodes"]}
            self.assertEqual(len(ids), len(diagram["nodes"]))
            for edge in diagram["edges"]:
                self.assertIn(edge["source"], ids)
                self.assertIn(edge["target"], ids)
        for query in ("dataset?bucket=year", "features?model=other", "features?limit=0", "features?limit=47"):
            self.assertEqual(self.client.get(f"/api/observatory/{query}").status_code, 422)
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/api/observatory/performance", schema["paths"])


if __name__ == "__main__":
    unittest.main()
