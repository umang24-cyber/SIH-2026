"""
Extended Forensic Services Unit & API Test Suite.
Uses standard Python unittest for zero-external-dependency execution.
Tests:
1. Streaming Sliding-Window Temporal Correlator (Out-of-Order Packet Reconciliation).
2. Tor & Obfuscated Network Telemetry Profiler (Shannon Timing Entropy).
3. Law Enforcement Section 91 Cr.P.C. / FIU-IND Dossier Generator (JSON & HTML).
100% Offline / Air-Gapped compliant.
"""
import unittest
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.streaming_correlator import streaming_correlator
from backend.app.services.tor_profiler import tor_profiler
from backend.app.services.dossier_service import dossier_service
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.ml_service import ml_service

class TestExtendedServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize all forensic engines once for tests."""
        if not data_service.is_ready:
            data_service.initialize()
            clustering_service.build_clusters()
            typology_detector.scan_all_typologies(max_candidates=20)
            ml_service.load_model()
        cls.client = TestClient(app)

    def test_01_streaming_reconciler_temporal_window(self):
        """Test out-of-order mempool and block frame matching via temporal sliding window."""
        mempool_stream = [
            {"txid": 101, "relay_timestamp": 1600000000.0, "relay_ip": "1.2.3.4", "asn": "AS1234", "is_tor": False},
            {"txid": 102, "relay_timestamp": 1600000010.0, "relay_ip": "5.6.7.8", "asn": "AS5678", "is_tor": True},
            {"txid": 103, "relay_timestamp": 1600000000.0, "relay_ip": "9.9.9.9", "asn": "AS9999", "is_tor": False},
            {"txid": 104, "relay_timestamp": 1600000050.0, "relay_ip": "4.4.4.4", "asn": "AS4444", "is_tor": False},
        ]
        block_stream = [
            {"txid": 101, "block_timestamp": 1600000015.0, "block_height": 700000, "btc_value": 1.5},
            {"txid": 102, "block_timestamp": 1600000012.0, "block_height": 700000, "btc_value": 0.5},
            {"txid": 103, "block_timestamp": 1600000200.0, "block_height": 700001, "btc_value": 3.0},
            {"txid": 105, "block_timestamp": 1600000020.0, "block_height": 700000, "btc_value": 0.1},
        ]

        res = streaming_correlator.reconcile_asynchronous_streams(
            mempool_stream=mempool_stream,
            block_stream=block_stream,
            max_window_seconds=60.0
        )

        summary = res["reconciliation_summary"]
        self.assertEqual(summary["total_mempool_frames"], 4)
        self.assertEqual(summary["total_block_events"], 4)
        self.assertEqual(summary["correlated_matches"], 3)  # exact ID 103 retained despite large timing gap
        self.assertEqual(summary["within_window_matches"], 2)
        self.assertEqual(summary["timing_issue_count"], 1)
        self.assertEqual(summary["orphan_mempool_packets"], 1)
        self.assertEqual(summary["orphan_block_events"], 1)
        self.assertGreater(summary["average_propagation_delta_seconds"], 0)

    def test_02_tor_entropy_calculation(self):
        """Verify Shannon Timing Entropy computation."""
        constant_deltas = [2.0, 2.0, 2.0, 2.0, 2.0]
        bot_entropy = tor_profiler.calculate_shannon_entropy(constant_deltas)
        self.assertEqual(bot_entropy, 0.0)

        random_deltas = [0.1, 1.5, 3.2, 8.4, 15.6, 22.1, 45.0]
        human_entropy = tor_profiler.calculate_shannon_entropy(random_deltas)
        self.assertGreater(human_entropy, 1.5)

    def test_03_tor_network_summary(self):
        """Verify aggregated Tor network profiling."""
        summary = tor_profiler.get_tor_network_summary()
        self.assertIn("total_tor_transactions", summary)
        self.assertIn("unique_tor_exit_nodes", summary)
        self.assertIn("tor_timing_entropy", summary)
        self.assertIn("top_tor_exit_countries", summary)
        self.assertIsInstance(summary["top_tor_exit_countries"], list)

    def test_04_dossier_service_json_and_html(self):
        """Verify system-generated investigation summary output."""
        sample_txid = next(iter(data_service.txid_map.keys()))
        
        # JSON Dossier
        dossier = dossier_service.generate_dossier(sample_txid)
        self.assertIn("case_metadata", dossier)
        self.assertIn("recommended_investigative_actions", dossier)
        self.assertIn("transaction_evidence", dossier)
        self.assertIn("network_telemetry_observation", dossier)
        self.assertIn("threat_assessment", dossier)
        self.assertGreaterEqual(len(dossier["recommended_investigative_actions"]), 3)
        self.assertEqual(dossier["case_metadata"]["data_status"], "Synthetic / Demonstration Dataset")
        self.assertEqual(dossier["case_metadata"]["model_status"], "V7 Frozen Synthetic Benchmark")

        # HTML Dossier
        html_doc = dossier_service.generate_html_dossier(sample_txid)
        self.assertIn("<!DOCTYPE html>", html_doc)
        self.assertIn("CONFIDENTIAL // SYSTEM-GENERATED DEMONSTRATION", html_doc)
        self.assertIn("System-generated recommendations", html_doc)
        self.assertIn(str(sample_txid), html_doc)

    def test_05_api_stream_endpoints(self):
        """Test API stream endpoints."""
        res_batch = self.client.get("/api/stream/batch?limit=10")
        self.assertEqual(res_batch.status_code, 200)
        data = res_batch.json()
        self.assertEqual(data["count"], 10)
        self.assertEqual(len(data["events"]), 10)

        req_payload = {
            "mempool_stream": [{"txid": 1, "relay_timestamp": 100.0, "relay_ip": "1.1.1.1"}],
            "block_stream": [{"txid": 1, "block_timestamp": 105.0, "btc_value": 0.5}],
            "max_window_seconds": 30.0
        }
        res_recon = self.client.post("/api/stream/reconcile", json=req_payload)
        self.assertEqual(res_recon.status_code, 200)
        self.assertEqual(res_recon.json()["reconciliation_summary"]["correlated_matches"], 1)

    def test_06_api_intel_tor_endpoints(self):
        """Test Tor intel endpoints."""
        res_summary = self.client.get("/api/intel/tor-summary")
        self.assertEqual(res_summary.status_code, 200)
        self.assertIn("tor_timing_entropy", res_summary.json())

        sample_txid = next(iter(data_service.txid_map.keys()))
        res_prof = self.client.get(f"/api/intel/tor-profiler/{sample_txid}")
        self.assertEqual(res_prof.status_code, 200)
        self.assertIn("obfuscation_evasion_score", res_prof.json())

    def test_07_api_dossier_endpoints(self):
        """Test LEA Dossier JSON and HTML export routes."""
        sample_txid = next(iter(data_service.txid_map.keys()))
        
        # JSON Route
        res_json = self.client.get(f"/api/dossier/{sample_txid}")
        self.assertEqual(res_json.status_code, 200)
        self.assertIn("case_metadata", res_json.json())

        # HTML Route
        res_html = self.client.get(f"/api/dossier/{sample_txid}/html")
        self.assertEqual(res_html.status_code, 200)
        self.assertIn("text/html", res_html.headers["content-type"])
        self.assertIn("SYSTEM-GENERATED DEMONSTRATION", res_html.text)

if __name__ == "__main__":
    unittest.main()
