"""
graph_engine/tests/test_phase1.py — Phase 1 unit tests.

Runnable without the real dataset.  All tests use a small synthetic sample
built inline.

Usage
-----
    python -m graph_engine.tests.test_phase1          # from project root
    python -m unittest graph_engine.tests.test_phase1 # alternative
"""

from __future__ import annotations

import logging
import unittest
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Suppress info-level log noise during tests; keep warnings/errors visible.
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.WARNING)

# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from graph_engine.ingest import (
    DEFAULT_FIELD_MAP,
    FieldMap,
    NetworkMeta,
    RawTxRecord,
    WalletEntry,
    adapt_row,
    validate_record,
)
from graph_engine import graph_build


# ===========================================================================
# Synthetic data helpers
# ===========================================================================

_TS_BLOCK  = datetime(2014, 3, 15, 9, 22, 41, tzinfo=timezone.utc)
_TS_RELAY  = datetime(2014, 3, 15, 9, 22, 40, 812000, tzinfo=timezone.utc)


def _make_raw_dict(
    *,
    txid: int             = 12345,
    timestamp             = _TS_BLOCK,
    input_addresses       = None,
    input_amounts         = None,
    output_addresses      = None,
    output_amounts        = None,
    fee_btc: float        = 0.0003,
    script_type: str      = "P2PKH",
    relay_ip: str         = "1.2.3.4",
    relay_timestamp       = _TS_RELAY,
    relay_port: int       = 8333,
    node_type: str        = "residential",
    country_code: str     = "IN",
    asn: str              = "AS55836",
    isp: str              = "Reliance Jio",
    user_agent: str       = "/Satoshi:22.0.0/",
    scenario_id: str      = "peel_001",
    split: str            = "train",
    is_illicit: int       = 0,
    pattern_type: str     = "normal",
) -> dict:
    return {
        "txid":             txid,
        "timestamp":        timestamp,
        "input_addresses":  input_addresses  if input_addresses  is not None else ["1ADDR_IN_A"],
        "input_amounts":    input_amounts    if input_amounts    is not None else [0.30],
        "output_addresses": output_addresses if output_addresses is not None else ["1ADDR_OUT_B"],
        "output_amounts":   output_amounts   if output_amounts   is not None else [0.2997],
        "fee_btc":          fee_btc,
        "script_type":      script_type,
        "relay_ip":         relay_ip,
        "relay_timestamp":  relay_timestamp,
        "relay_port":       relay_port,
        "node_type":        node_type,
        "country_code":     country_code,
        "asn":              asn,
        "isp":              isp,
        "user_agent":       user_agent,
        "scenario_id":      scenario_id,
        "split":            split,
        "is_illicit":       is_illicit,
        "pattern_type":     pattern_type,
    }


def _make_record(**kwargs) -> RawTxRecord:
    """Convenience: build a RawTxRecord from keyword overrides."""
    raw = _make_raw_dict(**kwargs)
    rec = adapt_row(raw)
    assert rec is not None, f"adapt_row returned None for: {raw}"
    return rec


def _build_multi_io_graph() -> tuple:
    """
    Synthetic 2-input / 2-output transaction + a separate single-input/output
    transaction for parallel-edge testing.

    Returns (G, P, tx1_id, tx2_id, in1, in2, out1, out2).
    """
    #
    # Transaction tx:9001  — 2 inputs, 2 outputs
    #   inputs:  [WALLET_A (0.50 BTC), WALLET_B (0.50 BTC)]
    #   outputs: [WALLET_C (0.40 BTC), WALLET_D (0.59 BTC)]
    #   fee:     0.01 BTC
    #
    rec1 = _make_record(
        txid=9001,
        input_addresses=["WALLET_A", "WALLET_B"],
        input_amounts=[0.50, 0.50],
        output_addresses=["WALLET_C", "WALLET_D"],
        output_amounts=[0.40, 0.59],
        fee_btc=0.01,
        relay_ip="10.0.0.1",
    )

    #
    # Transaction tx:9002  — 1 input, 1 output
    # Same sender pair (WALLET_A → WALLET_C) but different tx — tests parallel edges
    #   inputs:  [WALLET_A (0.20 BTC)]
    #   outputs: [WALLET_C (0.1997 BTC)]
    #   fee:     0.0003 BTC
    #
    rec2 = _make_record(
        txid=9002,
        input_addresses=["WALLET_A"],
        input_amounts=[0.20],
        output_addresses=["WALLET_C"],
        output_amounts=[0.1997],
        fee_btc=0.0003,
        relay_ip="10.0.0.2",
    )

    G = graph_build.build_full_graph_from_records([rec1, rec2])
    P = graph_build.build_wallet_projection(G)

    tx1_id = f"tx:9001"
    tx2_id = f"tx:9002"
    in1 = "w:WALLET_A"
    in2 = "w:WALLET_B"
    out1 = "w:WALLET_C"
    out2 = "w:WALLET_D"
    return G, P, tx1_id, tx2_id, in1, in2, out1, out2


# ===========================================================================
# Task 1 — RawTxRecord adapter tests
# ===========================================================================

class TestRawTxRecordAdapter(unittest.TestCase):

    # ---------------------------------------------------------------------- #
    def test_round_trip_valid_record(self):
        """Raw dict → adapt_row() → valid RawTxRecord with all fields intact."""
        raw = _make_raw_dict(
            txid=42,
            input_addresses=["ADDR_IN_1", "ADDR_IN_2"],
            input_amounts=[0.10, 0.20],
            output_addresses=["ADDR_OUT_1"],
            output_amounts=[0.2997],
            fee_btc=0.0003,
            script_type="P2WPKH",
            relay_ip="192.168.1.1",
            relay_port=9999,
            node_type="tor_exit_node",
            country_code="US",
            asn="AS1234",
            isp="SomeISP",
            user_agent="/Satoshi:21.0/",
            scenario_id="layer_007",
            split="test",
            is_illicit=1,
            pattern_type="layering",
        )
        rec = adapt_row(raw)

        self.assertIsNotNone(rec, "adapt_row should return a RawTxRecord for valid input")
        self.assertIsInstance(rec, RawTxRecord)

        # --- Transaction identity ---
        self.assertEqual(rec.txid, 42)
        self.assertEqual(rec.timestamp, _TS_BLOCK)

        # --- Inputs ---
        self.assertEqual(len(rec.inputs), 2)
        self.assertEqual(rec.inputs[0].address, "ADDR_IN_1")
        self.assertAlmostEqual(rec.inputs[0].amount_btc, 0.10, places=8)
        self.assertEqual(rec.inputs[1].address, "ADDR_IN_2")
        self.assertAlmostEqual(rec.inputs[1].amount_btc, 0.20, places=8)

        # --- Outputs ---
        self.assertEqual(len(rec.outputs), 1)
        self.assertEqual(rec.outputs[0].address, "ADDR_OUT_1")
        self.assertAlmostEqual(rec.outputs[0].amount_btc, 0.2997, places=8)

        # --- Scalars ---
        self.assertAlmostEqual(rec.fee_btc, 0.0003, places=8)
        self.assertEqual(rec.script_type, "P2WPKH")

        # --- Network meta ---
        self.assertEqual(rec.network.relay_ip, "192.168.1.1")
        self.assertEqual(rec.network.relay_port, 9999)
        self.assertEqual(rec.network.node_type, "tor_exit_node")
        self.assertEqual(rec.network.country_code, "US")
        self.assertEqual(rec.network.asn, "AS1234")
        self.assertEqual(rec.network.isp, "SomeISP")
        self.assertEqual(rec.network.user_agent, "/Satoshi:21.0/")

        # --- Optional passthrough ---
        self.assertEqual(rec.scenario_id, "layer_007")
        self.assertEqual(rec.split, "test")
        self.assertEqual(rec.is_illicit, 1)
        self.assertEqual(rec.pattern_type, "layering")

        # --- Derived properties ---
        self.assertEqual(rec.input_addresses, ["ADDR_IN_1", "ADDR_IN_2"])
        self.assertEqual(rec.output_addresses, ["ADDR_OUT_1"])
        self.assertAlmostEqual(rec.total_input_btc, 0.30, places=8)

    # ---------------------------------------------------------------------- #
    def test_missing_timestamp_rejected(self):
        """Record with null timestamp must be rejected (returns None)."""
        raw = _make_raw_dict()
        raw["timestamp"] = None
        rec = adapt_row(raw)
        self.assertIsNone(rec, "adapt_row should return None when timestamp is None")

    # ---------------------------------------------------------------------- #
    def test_empty_inputs_rejected(self):
        """Record with empty input list must be rejected."""
        raw = _make_raw_dict(
            input_addresses=[],
            input_amounts=[],
        )
        rec = adapt_row(raw)
        self.assertIsNone(rec, "adapt_row should return None when inputs are empty")

    # ---------------------------------------------------------------------- #
    def test_empty_outputs_rejected(self):
        """Record with empty output list must be rejected."""
        raw = _make_raw_dict(
            output_addresses=[],
            output_amounts=[],
        )
        rec = adapt_row(raw)
        self.assertIsNone(rec, "adapt_row should return None when outputs are empty")

    # ---------------------------------------------------------------------- #
    def test_change_address_overlap_warns_not_rejects(self):
        """
        An address appearing on both input and output sides (UTXO change-address
        reuse) must produce a valid record — only a warning is expected.
        """
        shared_addr = "SHARED_CHANGE_ADDR"
        raw = _make_raw_dict(
            input_addresses=[shared_addr, "OTHER_IN"],
            input_amounts=[0.50, 0.10],
            output_addresses=[shared_addr, "OTHER_OUT"],
            output_amounts=[0.40, 0.19],
            fee_btc=0.01,
        )
        with self.assertLogs(level="WARNING") as cm:
            rec = adapt_row(raw)

        self.assertIsNotNone(rec, "Change-address overlap should not reject the record")
        self.assertTrue(
            any("change-address reuse" in msg or "both input and output" in msg
                for msg in cm.output),
            "Expected a warning about change-address overlap",
        )

    # ---------------------------------------------------------------------- #
    def test_custom_field_map(self):
        """FieldMap correctly remaps non-standard column names."""
        custom_map = FieldMap(
            txid="tx_identifier",
            input_addresses="in_addrs",
            input_amounts="in_vals",
            output_addresses="out_addrs",
            output_amounts="out_vals",
            fee_btc="miner_fee",
            script_type="script",
            relay_ip="ip_addr",
            relay_timestamp="relay_ts",
            relay_port="port",
            node_type="infra_type",
        )
        raw = {
            "tx_identifier": 777,
            "timestamp":     _TS_BLOCK,
            "in_addrs":      ["ADDR_A"],
            "in_vals":       [0.5],
            "out_addrs":     ["ADDR_B"],
            "out_vals":      [0.4997],
            "miner_fee":     0.0003,
            "script":        "P2SH",
            "ip_addr":       "9.9.9.9",
            "relay_ts":      _TS_RELAY,
            "port":          8333,
            "infra_type":    "datacenter",
            "country_code":  "DE",
            "asn":           "AS13",
            "isp":           "Cloudflare",
            "user_agent":    "/Satoshi:22.0/",
        }
        rec = adapt_row(raw, custom_map)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.txid, 777)
        self.assertEqual(rec.script_type, "P2SH")
        self.assertEqual(rec.network.relay_ip, "9.9.9.9")


# ===========================================================================
# Task 2 — Full heterogeneous graph tests
# ===========================================================================

class TestBuildFullGraph(unittest.TestCase):

    def setUp(self):
        self.G, self.P, self.tx1, self.tx2, \
        self.in1, self.in2, self.out1, self.out2 = _build_multi_io_graph()

    # ---------------------------------------------------------------------- #
    def test_node_types_present(self):
        """G must contain wallet, transaction, and ip node types."""
        node_types = {
            data["node_type"]
            for _, data in self.G.nodes(data=True)
        }
        self.assertIn("wallet",      node_types)
        self.assertIn("transaction", node_types)
        self.assertIn("ip",          node_types)

    # ---------------------------------------------------------------------- #
    def test_edge_types_present(self):
        """G must contain SENT, RECEIVED, and BROADCAST edge types."""
        edge_types = set()
        for _, _, data in self.G.edges(data=True):
            edge_types.add(data.get("edge_type"))
        self.assertIn("SENT",      edge_types)
        self.assertIn("RECEIVED",  edge_types)
        self.assertIn("BROADCAST", edge_types)

    # ---------------------------------------------------------------------- #
    def test_bipartite_structure_holds(self):
        """verify_bipartite must pass (no direct wallet→wallet or tx→tx edges)."""
        ok, violations = graph_build.verify_bipartite(self.G)
        self.assertTrue(
            ok,
            f"Bipartite check failed with {len(violations)} violation(s): {violations}",
        )

    # ---------------------------------------------------------------------- #
    def test_multi_input_output_edge_counts(self):
        """
        tx:9001 (2 inputs, 2 outputs) should have:
        - exactly 2 SENT in-edges (from WALLET_A, WALLET_B)
        - exactly 2 RECEIVED out-edges (to WALLET_C, WALLET_D)
        - exactly 1 BROADCAST in-edge (from the relay IP)
        """
        # SENT in-edges to tx1
        sent_edges = [
            (u, v, d)
            for u, v, d in self.G.in_edges(self.tx1, data=True)
            if d.get("edge_type") == "SENT"
        ]
        self.assertEqual(
            len(sent_edges), 2,
            f"Expected 2 SENT edges into tx:9001, got {len(sent_edges)}",
        )

        # RECEIVED out-edges from tx1
        received_edges = [
            (u, v, d)
            for u, v, d in self.G.out_edges(self.tx1, data=True)
            if d.get("edge_type") == "RECEIVED"
        ]
        self.assertEqual(
            len(received_edges), 2,
            f"Expected 2 RECEIVED edges from tx:9001, got {len(received_edges)}",
        )

        # BROADCAST in-edges to tx1
        broadcast_edges = [
            (u, v, d)
            for u, v, d in self.G.in_edges(self.tx1, data=True)
            if d.get("edge_type") == "BROADCAST"
        ]
        self.assertEqual(
            len(broadcast_edges), 1,
            f"Expected 1 BROADCAST edge into tx:9001, got {len(broadcast_edges)}",
        )

    # ---------------------------------------------------------------------- #
    def test_transaction_node_attributes(self):
        """Transaction node in G must carry required metadata attributes."""
        tx_data = self.G.nodes[self.tx1]
        self.assertEqual(tx_data["node_type"],   "transaction")
        self.assertEqual(tx_data["txid"],         9001)
        self.assertAlmostEqual(tx_data["fee_btc"], 0.01, places=8)
        self.assertEqual(tx_data["script_type"],  "P2PKH")
        self.assertEqual(tx_data["num_inputs"],    2)
        self.assertEqual(tx_data["num_outputs"],   2)


# ===========================================================================
# Task 3 — Wallet-to-wallet projection tests
# ===========================================================================

class TestWalletProjection(unittest.TestCase):

    def setUp(self):
        self.G, self.P, self.tx1, self.tx2, \
        self.in1, self.in2, self.out1, self.out2 = _build_multi_io_graph()

    # ---------------------------------------------------------------------- #
    def test_edge_count_multi_io(self):
        """
        tx:9001 has 2 inputs × 2 outputs = 4 possible pairs.
        No self-loops (all addresses are distinct).
        So tx:9001 contributes exactly 4 wallet→wallet edges.
        tx:9002 has 1 input × 1 output = 1 edge.
        Total = 5 edges in P.
        """
        self.assertEqual(
            self.P.number_of_edges(), 5,
            f"Expected 5 edges in P, got {self.P.number_of_edges()}",
        )

    # ---------------------------------------------------------------------- #
    def test_edge_metadata_intact(self):
        """
        Every edge in P must carry: txid, amount_btc, timestamp, fee_btc,
        script_type.
        """
        required_keys = {"txid", "amount_btc", "timestamp", "fee_btc", "script_type"}
        for u, v, data in self.P.edges(data=True):
            missing = required_keys - set(data.keys())
            self.assertEqual(
                missing, set(),
                f"Edge {u}→{v} is missing metadata keys: {missing}",
            )

    # ---------------------------------------------------------------------- #
    def test_parallel_edges_not_collapsed(self):
        """
        WALLET_A → WALLET_C appears in both tx:9001 and tx:9002.
        P must contain exactly 2 parallel edges between them (MultiDiGraph).
        """
        edges_a_to_c = [
            data for _, _, data in self.P.edges(data=True)
            if _ == self.in1 and __ == self.out1
            # Use the edge iterator form below
        ]
        # Correct approach: iterate over all edges with data
        edges_a_to_c = [
            data
            for u, v, data in self.P.edges(data=True)
            if u == self.in1 and v == self.out1
        ]
        self.assertEqual(
            len(edges_a_to_c), 2,
            f"Expected 2 parallel edges from {self.in1} → {self.out1}, "
            f"got {len(edges_a_to_c)}",
        )
        # Verify they come from different transactions
        txids = {d["txid"] for d in edges_a_to_c}
        self.assertEqual(txids, {9001, 9002})

    # ---------------------------------------------------------------------- #
    def test_amounts_not_aggregated(self):
        """
        The two WALLET_A → WALLET_C edges must carry different amounts
        (not summed).  tx:9001 delivers 0.40 BTC; tx:9002 delivers 0.1997 BTC.
        """
        amounts = sorted([
            data["amount_btc"]
            for u, v, data in self.P.edges(data=True)
            if u == self.in1 and v == self.out1
        ])
        self.assertEqual(len(amounts), 2)
        self.assertAlmostEqual(amounts[0], 0.1997, places=4)
        self.assertAlmostEqual(amounts[1], 0.40,   places=4)

    # ---------------------------------------------------------------------- #
    def test_no_self_loops_in_projection(self):
        """No wallet→wallet self-loop edges should appear in P."""
        self_loops = [
            (u, v) for u, v in self.P.edges()
            if u == v
        ]
        self.assertEqual(
            self_loops, [],
            f"Unexpected self-loop(s) in P: {self_loops}",
        )

    # ---------------------------------------------------------------------- #
    def test_wallet_b_to_wallet_c_and_d_exist(self):
        """
        tx:9001 has WALLET_B as input and WALLET_C, WALLET_D as outputs.
        P must contain edges WALLET_B → WALLET_C and WALLET_B → WALLET_D.
        """
        b_to_c = [(u, v) for u, v in self.P.edges() if u == self.in2 and v == self.out1]
        b_to_d = [(u, v) for u, v in self.P.edges() if u == self.in2 and v == self.out2]
        self.assertGreaterEqual(len(b_to_c), 1, "Expected WALLET_B → WALLET_C edge in P")
        self.assertGreaterEqual(len(b_to_d), 1, "Expected WALLET_B → WALLET_D edge in P")


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
