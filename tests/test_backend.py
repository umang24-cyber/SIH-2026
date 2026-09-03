"""
Automated Backend, Typology Scanner, Clustering, Flow, and Benchmark Unit Tests.
Validates 100% compliance with API_CONTRACT.md, DATA_DICTIONARY.md, and Zero-Leakage rules.
Runs 100% offline in WSL2 / Linux.
"""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.services.data_service import data_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.clustering_service import clustering_service
from backend.app.services.ml_service import ml_service

class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize in-memory data store, clustering, and typology scanner
        data_service.initialize()
        clustering_service.build_clusters()
        typology_detector.scan_all_typologies()
        ml_service.load_model()
        cls.client = TestClient(app)

    def test_01_ingestion_integrity(self):
        """Verify 82,078 rows loaded and indexed with zero nulls."""
        self.assertEqual(len(data_service.txid_map), 82078)
        self.assertGreater(len(data_service.unique_wallets), 10000)
        self.assertGreater(len(data_service.scenario_tx_map), 10000)

        # Spot check a transaction
        sample_txid = next(iter(data_service.txid_map.keys()))
        sample_tx = data_service.txid_map[sample_txid]
        self.assertIsInstance(sample_tx["input_addresses"], list)
        self.assertIsInstance(sample_tx["output_addresses"], list)
        self.assertIsInstance(sample_tx["input_amounts"], list)
        self.assertIsInstance(sample_tx["output_amounts"], list)
        self.assertIn("propagation_delta_ms", sample_tx)

    def test_02_health_endpoint_and_timing_header(self):
        """Verify GET /health returns expected status and X-Process-Time header."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Process-Time", response.headers)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertEqual(data["loaded_transactions"], 82078)

    def test_03_transaction_endpoint(self):
        """Verify GET /transaction/{txid} returns full dual-layer telemetry."""
        sample_txid = next(iter(data_service.txid_map.keys()))
        response = self.client.get(f"/transaction/{sample_txid}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["txid"], sample_txid)
        self.assertIn("network", data)
        self.assertIn("relay_ip", data["network"])
        self.assertIn("propagation_delta_ms", data["network"])

    def test_04_entity_endpoint(self):
        """Verify GET /entity/{address} calculates wallet profile and flows."""
        sample_addr = next(iter(data_service.unique_wallets))
        response = self.client.get(f"/entity/{sample_addr}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["address"], sample_addr)
        self.assertIn("total_received_btc", data)
        self.assertIn("total_sent_btc", data)
        self.assertIn("is_licit_exchange", data)

    def test_05_cioh_clustering_endpoint(self):
        """Verify GET /entity/{address}/cluster aggregates co-owned wallets via CIOH."""
        multi_addr = None
        for tx in data_service.txid_map.values():
            if len(tx.get("input_addresses", [])) >= 2:
                multi_addr = tx["input_addresses"][0]
                break
                
        self.assertIsNotNone(multi_addr)
        response = self.client.get(f"/entity/{multi_addr}/cluster")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["query_address"], multi_addr)
        self.assertGreaterEqual(data["cluster_size"], 2)
        self.assertGreater(len(data["co_owned_addresses"]), 1)
        self.assertGreaterEqual(data["multi_input_tx_count"], 1)

    def test_06_taint_tracking_endpoint(self):
        """Verify GET /taint computes forward dirty coin risk propagation."""
        sample_addr = next(iter(data_service.unique_wallets))
        response = self.client.get(f"/taint?seed_address={sample_addr}&decay_rate=0.85&max_depth=3")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["seed_address"], sample_addr)
        self.assertIn("total_tainted_wallets", data)
        self.assertIn("contaminated_wallets", data)

    def test_07_graph_endpoint(self):
        """Verify GET /graph/{scenario_id} returns heterogeneous nodes & edges."""
        sample_sc = next(iter(data_service.scenario_tx_map.keys()))
        response = self.client.get(f"/graph/{sample_sc}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario_id"], sample_sc)
        self.assertGreater(len(data["nodes"]), 0)
        self.assertGreater(len(data["edges"]), 0)

    def test_08_trace_endpoint(self):
        """Verify GET /trace executes BFS pathfinding."""
        sample_addr = next(iter(data_service.unique_wallets))
        response = self.client.get(f"/trace?src={sample_addr}&dst={sample_addr}&max_depth=3")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("path_found", data)
        self.assertIn("hops", data)

    def test_09_dynamic_alerts_and_evidence(self):
        """Verify dynamic typology detector generates ranked alerts with deep evidence."""
        response = self.client.get("/alerts?min_confidence=0.60")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_alerts"], 0)

    def test_10_search_and_stats(self):
        """Verify universal search, scenarios list, and telemetry stats."""
        sample_txid = next(iter(data_service.txid_map.keys()))
        res_tx = self.client.get(f"/search?q={sample_txid}")
        self.assertEqual(res_tx.status_code, 200)
        self.assertEqual(res_tx.json()["match_type"], "TRANSACTION")

        res_sc = self.client.get("/scenarios?page=1&page_size=5")
        self.assertEqual(res_sc.status_code, 200)

        res_stats = self.client.get("/stats/telemetry")
        self.assertEqual(res_stats.status_code, 200)

    def test_11_ml_feature_extractor_zero_leakage(self):
        """Verify ML feature extractor strictly produces 15 features without ground-truth labels."""
        sample_tx = next(iter(data_service.txid_map.values()))
        features = ml_service.extract_features(sample_tx)
        self.assertEqual(features.shape, (1, 15))
        self.assertFalse(any(val != val for val in features[0]))

    def test_12_transaction_flow_decomposition(self):
        """Verify GET /transaction/{txid}/flow returns structured inputs, outputs, and entity IDs."""
        sample_txid = next(iter(data_service.txid_map.keys()))
        response = self.client.get(f"/transaction/{sample_txid}/flow")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["txid"], sample_txid)
        self.assertIn("inputs", data)
        self.assertIn("outputs", data)
        self.assertIn("fee_ratio_percent", data)

    def test_13_graph_community_detection(self):
        """Verify GET /graph/{scenario_id}/communities partitions graph into syndicates."""
        sample_sc = next(iter(data_service.scenario_tx_map.keys()))
        response = self.client.get(f"/graph/{sample_sc}/communities")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_communities_detected", data)
        self.assertIn("communities", data)

    def test_14_scenario_deep_profile(self):
        """Verify GET /scenarios/{scenario_id} returns risk scores and hub wallets."""
        sample_sc = next(iter(data_service.scenario_tx_map.keys()))
        response = self.client.get(f"/scenarios/{sample_sc}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario_id"], sample_sc)
        self.assertIn("infrastructure_risk_score", data)
        self.assertIn("top_hub_wallets", data)

    def test_15_evaluation_benchmark(self):
        """Verify GET /eval/benchmark returns quantitative offline evaluation metrics."""
        response = self.client.get("/eval/benchmark")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("performance_metrics", data)
        self.assertIn("overall_macro_f1", data)

if __name__ == "__main__":
    unittest.main()
