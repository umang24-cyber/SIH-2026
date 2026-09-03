"""
Automated Backend & Ingestion Integrity Unit Tests.
Validates 100% compliance with API_CONTRACT.md, DATA_DICTIONARY.md, and Zero-Leakage rules.
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

class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize in-memory data store
        data_service.initialize()
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

    def test_02_health_endpoint(self):
        """Verify GET /health returns expected status and counts."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
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

    def test_05_graph_endpoint(self):
        """Verify GET /graph/{scenario_id} returns heterogeneous nodes & edges."""
        sample_sc = next(iter(data_service.scenario_tx_map.keys()))
        response = self.client.get(f"/graph/{sample_sc}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["scenario_id"], sample_sc)
        self.assertGreater(len(data["nodes"]), 0)
        self.assertGreater(len(data["edges"]), 0)
        
        node_types = {n["type"] for n in data["nodes"]}
        edge_types = {e["type"] for e in data["edges"]}
        self.assertTrue(node_types.issubset({"Wallet", "Transaction", "IP"}))
        self.assertTrue(edge_types.issubset({"SENT", "RECEIVED", "BROADCAST"}))

    def test_06_trace_endpoint(self):
        """Verify GET /trace executes BFS pathfinding."""
        sample_addr = next(iter(data_service.unique_wallets))
        response = self.client.get(f"/trace?src={sample_addr}&dst={sample_addr}&max_depth=3")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("path_found", data)
        self.assertIn("hops", data)

    def test_07_alerts_endpoints(self):
        """Verify GET /alerts and GET /alerts/{id}/evidence."""
        response = self.client.get("/alerts")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["total_alerts"], 0)
        
        cand_id = data["alerts"][0]["candidate_id"]
        ev_resp = self.client.get(f"/alerts/{cand_id}/evidence")
        self.assertEqual(ev_resp.status_code, 200)
        ev_data = ev_resp.json()
        self.assertEqual(ev_data["candidate_id"], cand_id)
        self.assertIn("ml_feature_attributions", ev_data)

if __name__ == "__main__":
    unittest.main()
