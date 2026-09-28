"""Regression tests for exact ID association and descriptive timing evidence."""
import io
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes_ingest import router as ingest_router
from backend.app.api.routes_stream import router as stream_router
from backend.app.models.schemas import IngestScenarioAnalysis
from backend.app.services.streaming_correlator import StreamingCorrelator


def ledger(rows):
    header = "txid,timestamp,input_addresses,output_addresses,input_amounts,output_amounts,fee_btc,scenario_id\n"
    return (header + "".join(f'{txid},{timestamp},"[""a""]","[""b""]","[1]","[0.999]",0.001,case_a\n'
                             for txid, timestamp in rows)).encode()


def network(rows):
    header = "txid,relay_timestamp,relay_ip,asn,node_type\n"
    return (header + "".join(f"{txid},{timestamp},{ip},AS42,residential\n" for txid, timestamp, ip in rows)).encode()


class CorrelationEvidenceTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(ingest_router)
        app.include_router(stream_router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.store = MagicMock()
        self.store.txid_map = {}
        self.store.scenario_tx_map = {}
        self.store.add_transactions_batch.side_effect = lambda records: len(records)
        self.patcher = patch("backend.app.api.routes_ingest.data_service", self.store)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        analyze = patch("backend.app.api.routes_ingest._analyze_uploaded_scenario", side_effect=lambda sid, txs: IngestScenarioAnalysis(
            scenario_id=sid, transaction_count=len(txs), analysis_status="UNAVAILABLE"))
        analyze.start()
        self.addCleanup(analyze.stop)

    def upload(self, ledger_rows, network_rows, window=120):
        return self.client.post(f"/api/ingest/correlate?max_window_seconds={window}", files={
            "ledger_file": ("ledger.csv", ledger(ledger_rows), "text/csv"),
            "network_file": ("network.csv", network(network_rows), "text/csv"),
        })

    def test_same_id_large_gap_still_matches_and_delay_is_recomputed(self):
        response = self.upload([("987654321", "2026-09-06 14:22:10")], [("987654321", "2026-09-06 14:12:10", "1.2.3.4")])
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertEqual(data["matched_records"], 1)
        self.assertEqual(data["timing_issue_count"], 1)
        item = data["correlation_evidence"][0]
        self.assertEqual(item["timing_delta_seconds"], 600)
        self.assertEqual(item["timing_status"], "OUTSIDE_WINDOW")
        self.assertEqual(item["match_method"], "EXACT_TRANSACTION_ID")
        self.assertIsNone(item["correlation_confidence"])
        indexed = self.store.add_transactions_batch.call_args.args[0][0]
        self.assertEqual(indexed["propagation_delta_ms"], 600000)
        self.assertEqual(indexed["transaction_hash"], "987654321")

    def test_near_timestamps_different_ids_do_not_match(self):
        data = self.upload([("101", "2026-09-06 14:22:10")], [("102", "2026-09-06 14:22:10", "1.2.3.4")]).json()
        self.assertEqual(data["matched_records"], 0)
        self.assertEqual(data["unmatched_ledger"], 1)
        self.assertEqual(data["unmatched_network"], 1)
        self.assertEqual(len(self.store.add_transactions_batch.call_args.args[0]), 1)  # never index network-only placeholder

    def test_incomplete_scenario_is_not_scored_as_if_network_were_observed(self):
        result = self.upload([("101", "2026-09-06 14:22:10"), ("102", "2026-09-06 14:22:11")],
                             [("101", "2026-09-06 14:22:09", "1.2.3.4")]).json()
        self.assertEqual(result["scenario_results"][0]["analysis_status"], "UNAVAILABLE")
        self.assertIsNone(result["scenario_results"][0]["risk_score"])
        self.assertIn("Incomplete dual-stream", result["scenario_results"][0]["analysis_message"])

    def test_repeated_relay_observations_are_kept(self):
        data = self.upload([("123", "2026-09-06 14:22:10")], [
            ("123", "2026-09-06 14:22:09", "1.1.1.1"),
            ("123", "2026-09-06 14:22:08", "2.2.2.2"),
        ]).json()
        item = data["correlation_evidence"][0]
        self.assertEqual(data["matched_records"], 1)
        self.assertEqual(len(item["observations"]), 2)
        self.assertEqual(item["timing_delta_seconds"], 2)
        indexed = self.store.add_transactions_batch.call_args.args[0][0]
        self.assertEqual(indexed["relay_ip"], "2.2.2.2")
        self.assertEqual(len(indexed["relay_observations"]), 2)

    def test_missing_or_reversed_time_is_not_fabricated(self):
        missing_result = self.upload([("456", "")], [("456", "", "1.2.3.4")]).json()
        missing = missing_result["correlation_evidence"][0]
        self.assertEqual(missing["timing_status"], "MISSING_TIMESTAMP")
        self.assertIsNone(missing["timing_delta_seconds"])
        self.assertEqual(missing_result["scenario_results"][0]["analysis_status"], "UNAVAILABLE")
        reversed_time = self.upload([("457", "2026-09-06 14:22:10")],
                                    [("457", "2026-09-06 14:22:11", "1.2.3.4")]).json()["correlation_evidence"][0]
        self.assertEqual(reversed_time["timing_status"], "CLOCK_ORDER_ISSUE")
        self.assertEqual(reversed_time["timing_delta_seconds"], -1)

    def test_conflicting_ledger_rows_are_not_indexed(self):
        data = self.upload([("123", "2026-09-06 14:22:10"), ("123", "2026-09-06 14:22:11")],
                           [("123", "2026-09-06 14:22:09", "1.2.3.4")]).json()
        self.assertEqual(data["conflicting_records"], 1)
        self.assertEqual(data["matched_records"], 0)
        self.assertEqual(data["correlation_evidence"][0]["match_status"], "CONFLICTING")
        self.store.add_transactions_batch.assert_called_once_with([])

    def test_original_ids_are_preserved_and_internal_collisions_fail(self):
        long_hash = "ab" * 32
        result = self.upload([(long_hash, "2026-09-06 14:22:10")], [(long_hash, "2026-09-06 14:22:09", "1.2.3.4")])
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.json()["correlation_evidence"][0]["transaction_hash"], long_hash)
        self.assertEqual(self.store.add_transactions_batch.call_args.args[0][0]["transaction_hash"], long_hash)
        normalized = self.store.add_transactions_batch.call_args.args[0][0]
        self.store.txid_map = {normalized["txid"]: {"txid": normalized["txid"], "transaction_hash": "other"}}
        other = self.upload([(long_hash, "2026-09-06 14:22:10")], [(long_hash, "2026-09-06 14:22:09", "1.2.3.4")])
        self.assertEqual(other.status_code, 409)

    def test_stream_uses_same_rules_and_rejects_invalid_window(self):
        data = self.client.post("/api/stream/reconcile", json={
            "mempool_stream": [{"txid": "abc", "relay_timestamp": 100, "relay_ip": "1.2.3.4", "is_tor": "false"},
                               {"txid": "abc", "relay_timestamp": 90, "relay_ip": "2.3.4.5"}],
            "block_stream": [{"txid": "abc", "block_timestamp": 300}], "max_window_seconds": 120,
        }).json()
        self.assertEqual(data["reconciliation_summary"]["correlated_matches"], 1)
        self.assertEqual(data["reconciliation_summary"]["timing_issue_count"], 1)
        item = data["correlated_events"][0]
        self.assertEqual(item["timing_delta_seconds"], 210)
        self.assertEqual(item["timing_status"], "OUTSIDE_WINDOW")
        self.assertEqual(len(item["observations"]), 2)
        self.assertFalse(item["is_tor"])
        self.assertIsNone(item["correlation_confidence"])
        self.assertEqual(self.client.post("/api/stream/reconcile", json={
            "mempool_stream": [], "block_stream": [], "max_window_seconds": 0,
        }).status_code, 422)

    def test_migration_persists_original_hash_and_all_relay_observations(self):
        from backend.app.db.schema import create_schema, CREATE_TABLES_SQL
        from backend.app.services.db_service import DBService

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forensic.db"

            @contextmanager
            def connect():
                conn = sqlite3.connect(path)
                conn.row_factory = sqlite3.Row
                try:
                    yield conn
                finally:
                    conn.close()

            # Simulate an existing installation whose table predates the evidence columns.
            with connect() as conn:
                conn.executescript(CREATE_TABLES_SQL.replace("    transaction_hash TEXT,\n", "").replace("    relay_observations TEXT,\n", ""))
            with patch("backend.app.db.schema.get_db_connection", connect), patch("backend.app.services.db_service.get_db_connection", connect):
                create_schema()
                db = DBService()
                db.ensure_initialized = lambda: None
                record = dict(txid=123, transaction_hash="ab" * 32,
                              timestamp="2026-09-06 14:22:10", relay_timestamp="2026-09-06 14:22:08",
                              scenario_id="case_a", relay_observations=[
                                  {"relay_timestamp": "2026-09-06T14:22:08Z", "relay_ip": "1.2.3.4"},
                                  {"relay_timestamp": "2026-09-06T14:22:09Z", "relay_ip": "2.3.4.5"},
                              ])
                db.save_transactions_batch([record])
                loaded = db.load_all_custom_transactions()
                self.assertEqual(loaded[0]["transaction_hash"], record["transaction_hash"])
                self.assertEqual(loaded[0]["relay_observations"], record["relay_observations"])

    def test_stream_duplicate_conflicting_blocks_do_not_inflate_coverage(self):
        result = StreamingCorrelator().reconcile_asynchronous_streams(
            [{"txid": "abc", "relay_timestamp": 100}],
            [{"txid": "abc", "block_timestamp": 110}, {"txid": "abc", "block_timestamp": 120}],
        )
        summary = result["reconciliation_summary"]
        self.assertEqual(summary["correlated_matches"], 0)
        self.assertEqual(summary["conflicting_records"], 1)
        self.assertEqual(result["correlated_events"][0]["match_status"], "CONFLICTING")


if __name__ == "__main__":
    unittest.main()
