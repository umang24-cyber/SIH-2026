"""
graph_engine/tests/test_phase2.py — Phase 2 unit tests.

Tests the upgraded peeling chain detector, layering detector, deduplication helper,
and feature enrichment pipeline.

Usage
-----
    python -m unittest graph_engine.tests.test_phase2
"""

from __future__ import annotations

import logging
import unittest
from datetime import datetime, timedelta, timezone

import networkx as nx
import pandas as pd

from graph_engine import config, graph_build
from graph_engine.detectors import dedup, layering, peeling_chain
from graph_engine.features import enrich_and_build_dataframe
from graph_engine.ingest import NetworkMeta, RawTxRecord, WalletEntry
from graph_engine.structures import CandidateStructure

logging.basicConfig(level=logging.WARNING)

_T0 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_tx_record(
    txid: int,
    inputs: list[tuple[str, float]],
    outputs: list[tuple[str, float]],
    ts: datetime = _T0,
    fee_btc: float = 0.0001,
    script_type: str = "P2PKH",
    relay_ip: str = "10.0.0.1",
    asn: str = "AS1234",
    node_type_infra: str = "residential",
) -> RawTxRecord:
    """Helper to create a RawTxRecord for test graph building."""
    in_entries = [WalletEntry(address=addr, amount_btc=amt) for addr, amt in inputs]
    out_entries = [WalletEntry(address=addr, amount_btc=amt) for addr, amt in outputs]
    net = NetworkMeta(
        relay_ip=relay_ip,
        relay_timestamp=ts - timedelta(seconds=1),
        relay_port=8333,
        node_type=node_type_infra,
        country_code="US",
        asn=asn,
        isp="ISP Provider",
        user_agent="/Satoshi:22.0.0/",
    )
    return RawTxRecord(
        txid=txid,
        timestamp=ts,
        inputs=in_entries,
        outputs=out_entries,
        fee_btc=fee_btc,
        script_type=script_type,
        network=net,
    )


# ===========================================================================
# 1. Test Decay Score Computation
# ===========================================================================

class TestDecayScore(unittest.TestCase):
    """Unit tests for the log-linear decay consistency score."""

    def test_decay_score_perfect_geometric_decay(self):
        # Monotone exponential decay: 10 * 0.8^i
        amounts = [10.0, 8.0, 6.4, 5.12, 4.096]
        score = peeling_chain.compute_decay_score(amounts)
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_decay_score_flat_amounts(self):
        # Flat carry amount -> zero decay -> score 0.0
        amounts = [10.0, 10.0, 10.0, 10.0]
        score = peeling_chain.compute_decay_score(amounts)
        self.assertEqual(score, 0.0)

    def test_decay_score_strictly_increasing(self):
        # Increasing amounts -> not a peel decay -> score 0.0
        amounts = [1.0, 2.0, 3.0, 4.0]
        score = peeling_chain.compute_decay_score(amounts)
        self.assertEqual(score, 0.0)

    def test_decay_score_single_element(self):
        score = peeling_chain.compute_decay_score([10.0])
        self.assertEqual(score, 1.0)

    def test_decay_score_two_elements(self):
        score = peeling_chain.compute_decay_score([10.0, 8.0])
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_decay_score_noisy_decay(self):
        # Monotonically decreasing with slight deviations in decay rate
        amounts = [10.0, 7.0, 5.5, 4.0, 2.0]
        score = peeling_chain.compute_decay_score(amounts)
        # All steps decrease (monotonicity=1.0), R^2 is very high (>0.95)
        self.assertGreater(score, 0.90)


# ===========================================================================
# 2. Test Peeling Chain Detector
# ===========================================================================

class TestPeelingChainDetector(unittest.TestCase):
    """Tests for peeling_chain detector upgrades."""

    def test_clean_5_hop_peeling_chain(self):
        # 5 consecutive peel transactions:
        # Hop 1: W0 -> (W1: 9.0, P1: 1.0)
        # Hop 2: W1 -> (W2: 8.0, P2: 1.0)
        # Hop 3: W2 -> (W3: 7.0, P3: 1.0)
        # Hop 4: W3 -> (W4: 6.0, P4: 1.0)
        # Hop 5: W4 -> (W5: 5.0, P5: 1.0)
        records = [
            _make_tx_record(101, [("W0", 10.0)], [("W1", 9.0), ("P1", 1.0)], ts=_T0),
            _make_tx_record(102, [("W1", 9.0)], [("W2", 8.0), ("P2", 1.0)], ts=_T0 + timedelta(hours=1)),
            _make_tx_record(103, [("W2", 8.0)], [("W3", 7.0), ("P3", 1.0)], ts=_T0 + timedelta(hours=2)),
            _make_tx_record(104, [("W3", 7.0)], [("W4", 6.0), ("P4", 1.0)], ts=_T0 + timedelta(hours=3)),
            _make_tx_record(105, [("W4", 6.0)], [("W5", 5.0), ("P5", 1.0)], ts=_T0 + timedelta(hours=4)),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = peeling_chain.detect(G, P)
        self.assertEqual(len(candidates), 1)

        cand = candidates[0]
        self.assertEqual(cand.candidate_type, "peeling_chain")
        self.assertEqual(cand.member_txids, [101, 102, 103, 104, 105])
        self.assertEqual(cand.features["chain_length"], 5)
        self.assertAlmostEqual(cand.features["total_peeled_btc"], 5.0, places=4)
        self.assertGreaterEqual(cand.features["decay_consistency_score"], 0.9)
        self.assertIsNotNone(cand.hop_sequence)
        self.assertEqual(len(cand.hop_sequence), 5)

        # Check first and last hop in hop_sequence
        self.assertEqual(cand.hop_sequence[0]["from_wallet"], "W0")
        self.assertEqual(cand.hop_sequence[0]["to_wallet"], "W1")
        self.assertEqual(cand.hop_sequence[0]["txid"], 101)
        self.assertEqual(cand.hop_sequence[-1]["to_wallet"], "W5")

    def test_equal_split_rejected_by_asymmetry_ratio(self):
        # 50/50 splits: carry/peeled ratio = 1.0 < default 2.0
        records = [
            _make_tx_record(201, [("W0", 10.0)], [("W1", 5.0), ("P1", 5.0)], ts=_T0),
            _make_tx_record(202, [("W1", 5.0)], [("W2", 2.5), ("P2", 2.5)], ts=_T0 + timedelta(hours=1)),
            _make_tx_record(203, [("W2", 2.5)], [("W3", 1.25), ("P3", 1.25)], ts=_T0 + timedelta(hours=2)),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = peeling_chain.detect(G, P)
        self.assertEqual(len(candidates), 0)

    def test_asymmetry_ratio_overridable(self):
        # 60/40 splits: ratio = 6.0 / 4.0 = 1.5
        records = [
            _make_tx_record(301, [("W0", 10.0)], [("W1", 6.0), ("P1", 4.0)], ts=_T0),
            _make_tx_record(302, [("W1", 6.0)], [("W2", 3.6), ("P2", 2.4)], ts=_T0 + timedelta(hours=1)),
            _make_tx_record(303, [("W2", 3.6)], [("W3", 2.16), ("P3", 1.44)], ts=_T0 + timedelta(hours=2)),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        # Default ratio is 2.0 -> should be rejected
        cands_default = peeling_chain.detect(G, P)
        self.assertEqual(len(cands_default), 0)

        # Overridden ratio = 1.4 -> should be accepted
        cands_custom = peeling_chain.detect(G, P, min_asymmetry_ratio=1.4)
        self.assertEqual(len(cands_custom), 1)
        self.assertEqual(cands_custom[0].features["chain_length"], 3)

    def test_multi_input_disambiguation_picks_largest(self):
        # Multi-input seed: W_large contributes 9.0 BTC, W_small contributes 1.0 BTC
        records = [
            _make_tx_record(401, [("W_small", 1.0), ("W_large", 9.0)], [("W1", 8.0), ("P1", 2.0)], ts=_T0),
            _make_tx_record(402, [("W1", 8.0)], [("W2", 6.0), ("P2", 2.0)], ts=_T0 + timedelta(hours=1)),
            _make_tx_record(403, [("W2", 6.0)], [("W3", 4.0), ("P3", 2.0)], ts=_T0 + timedelta(hours=2)),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = peeling_chain.detect(G, P)
        self.assertEqual(len(candidates), 1)
        cand = candidates[0]
        # Primary from_wallet of hop 1 must be W_large
        self.assertEqual(cand.hop_sequence[0]["from_wallet"], "W_large")

    def test_hop_gap_exceeded_breaks_chain(self):
        # Hop 3 occurs 24 hours after Hop 2 (exceeding default 6h gap)
        records = [
            _make_tx_record(501, [("W0", 10.0)], [("W1", 9.0), ("P1", 1.0)], ts=_T0),
            _make_tx_record(502, [("W1", 9.0)], [("W2", 8.0), ("P2", 1.0)], ts=_T0 + timedelta(hours=1)),
            _make_tx_record(503, [("W2", 8.0)], [("W3", 7.0), ("P3", 1.0)], ts=_T0 + timedelta(hours=25)),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = peeling_chain.detect(G, P)
        # Chain only reached 2 hops before breaking -> below min_chain_length (3)
        self.assertEqual(len(candidates), 0)


# ===========================================================================
# 3. Test Layering Detector
# ===========================================================================

class TestLayeringDetector(unittest.TestCase):
    """Tests for layering detector upgrades."""

    def test_clean_5_branch_layering_detected(self):
        # Source S fans out to R1..R5 (5 txs)
        # R1..R5 each fan in to Sink C (5 txs)
        records = []
        for i in range(1, 6):
            # Fan out
            records.append(_make_tx_record(
                txid=1000 + i,
                inputs=[("S", 10.0)],
                outputs=[(f"R{i}", 9.9)],
                ts=_T0,
            ))
            # Fan in
            records.append(_make_tx_record(
                txid=2000 + i,
                inputs=[(f"R{i}", 9.9)],
                outputs=[("Sink", 9.8)],
                ts=_T0 + timedelta(hours=2),
            ))

        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = layering.detect(G, P)
        self.assertEqual(len(candidates), 1)

        cand = candidates[0]
        self.assertEqual(cand.candidate_type, "layering")
        self.assertEqual(cand.features["fan_out_degree"], 5)
        self.assertEqual(cand.features["fan_in_degree"], 5)
        self.assertEqual(cand.features["reconvergence_ratio"], 1.0)
        self.assertAlmostEqual(cand.features["amount_conservation_ratio"], (5 * 9.8) / (5 * 9.9), places=4)

        # Check hop_sequence details
        self.assertIsNotNone(cand.hop_sequence)
        self.assertEqual(len(cand.hop_sequence), 5)
        for branch in cand.hop_sequence:
            self.assertEqual(branch["origin"], "S")
            self.assertEqual(branch["sink"], "Sink")
            self.assertEqual(len(branch["intermediate_wallets"]), 1)
            self.assertEqual(len(branch["txids"]), 2)

    def test_divergent_paths_no_reconvergence(self):
        # S fans out to R1..R5, but each Ri sends to a distinct wallet D_i
        records = []
        for i in range(1, 6):
            records.append(_make_tx_record(
                txid=3000 + i,
                inputs=[("S", 10.0)],
                outputs=[(f"R{i}", 9.9)],
                ts=_T0,
            ))
            records.append(_make_tx_record(
                txid=4000 + i,
                inputs=[(f"R{i}", 9.9)],
                outputs=[(f"D{i}", 9.8)],
                ts=_T0 + timedelta(hours=1),
            ))

        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = layering.detect(G, P)
        self.assertEqual(len(candidates), 0)

    def test_temporal_hop_gap_pruning(self):
        # 5 branches fan out at T0.
        # R1, R2, R3 reach Sink within 2 hours.
        # R4, R5 reach Sink 100 hours later (exceeding 72h max hop gap).
        records = []
        for i in range(1, 6):
            records.append(_make_tx_record(
                txid=5000 + i,
                inputs=[("S", 10.0)],
                outputs=[(f"R{i}", 9.9)],
                ts=_T0,
            ))
            delay_hours = 2 if i <= 3 else 100
            records.append(_make_tx_record(
                txid=6000 + i,
                inputs=[(f"R{i}", 9.9)],
                outputs=[("Sink", 9.8)],
                ts=_T0 + timedelta(hours=delay_hours),
            ))

        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = layering.detect(G, P)
        # 3 out of 5 reconverge in time -> ratio = 0.6 >= LAYER_MIN_RECONVERGENCE_RATIO (0.6)
        self.assertEqual(len(candidates), 1)
        cand = candidates[0]
        self.assertEqual(cand.features["fan_in_degree"], 3)
        self.assertEqual(cand.features["reconvergence_ratio"], 0.6)
        self.assertEqual(len(cand.hop_sequence), 3)

    def test_exchange_hub_sink_filtered(self):
        # Create standard 5-branch layering to Sink
        records = []
        for i in range(1, 6):
            records.append(_make_tx_record(
                txid=7000 + i,
                inputs=[("S", 10.0)],
                outputs=[(f"R{i}", 9.9)],
                ts=_T0,
            ))
            records.append(_make_tx_record(
                txid=8000 + i,
                inputs=[(f"R{i}", 9.9)],
                outputs=[("ExchangeSink", 9.8)],
                ts=_T0 + timedelta(hours=1),
            ))

        # Add 600 dummy transactions involving ExchangeSink to exceed threshold (500)
        for k in range(600):
            records.append(_make_tx_record(
                txid=90000 + k,
                inputs=[("ExchangeSink", 0.01)],
                outputs=[(f"User_{k}", 0.009)],
                ts=_T0 + timedelta(minutes=k),
            ))

        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        candidates = layering.detect(G, P)
        # ExchangeSink should be filtered out
        self.assertEqual(len(candidates), 0)


# ===========================================================================
# 4. Test Deduplication
# ===========================================================================

class TestDedup(unittest.TestCase):
    """Tests for maximal chain and multi-typology deduplication."""

    def test_merge_maximal_chains_prunes_strict_subsets(self):
        cand_short = CandidateStructure(
            candidate_id="peel_0001",
            candidate_type="peeling_chain",
            member_txids=[101, 102],
        )
        cand_long = CandidateStructure(
            candidate_id="peel_0002",
            candidate_type="peeling_chain",
            member_txids=[101, 102, 103, 104],
        )
        cand_disjoint = CandidateStructure(
            candidate_id="peel_0003",
            candidate_type="peeling_chain",
            member_txids=[201, 202, 203],
        )

        merged = dedup.merge_maximal_chains([cand_short, cand_long, cand_disjoint])
        self.assertEqual(len(merged), 2)
        self.assertNotIn(cand_short, merged)
        self.assertIn(cand_long, merged)
        self.assertIn(cand_disjoint, merged)

    def test_merge_maximal_chains_handles_exact_duplicates(self):
        cand_a = CandidateStructure(
            candidate_id="peel_0001",
            candidate_type="peeling_chain",
            member_txids=[1, 2, 3],
        )
        cand_b = CandidateStructure(
            candidate_id="peel_0002",
            candidate_type="peeling_chain",
            member_txids=[1, 2, 3],
        )
        merged = dedup.merge_maximal_chains([cand_a, cand_b])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].candidate_id, "peel_0001")

    def test_merge_all_preserves_cross_typology_overlaps(self):
        cand_peel = CandidateStructure(
            candidate_id="peel_0001",
            candidate_type="peeling_chain",
            member_txids=[1, 2, 3],
        )
        cand_layer = CandidateStructure(
            candidate_id="layer_0001",
            candidate_type="layering",
            member_txids=[1, 2, 3],
        )

        merged = dedup.merge_all([cand_peel, cand_layer])
        self.assertEqual(len(merged), 2)
        types = {c.candidate_type for c in merged}
        self.assertEqual(types, {"peeling_chain", "layering"})


# ===========================================================================
# 5. Test Features Integration
# ===========================================================================

class TestFeaturesIntegration(unittest.TestCase):
    """Tests that features DataFrame contains decay_consistency_score and network features."""

    def test_dataframe_contains_decay_consistency_score(self):
        records = [
            _make_tx_record(101, [("W0", 10.0)], [("W1", 9.0), ("P1", 1.0)], ts=_T0, relay_ip="192.168.1.1", node_type_infra="tor_exit_node"),
            _make_tx_record(102, [("W1", 9.0)], [("W2", 8.0), ("P2", 1.0)], ts=_T0 + timedelta(hours=1), relay_ip="192.168.1.2", node_type_infra="tor_exit_node"),
            _make_tx_record(103, [("W2", 8.0)], [("W3", 7.0), ("P3", 1.0)], ts=_T0 + timedelta(hours=2), relay_ip="192.168.1.3", node_type_infra="residential"),
        ]
        G = graph_build.build_full_graph_from_records(records)
        P = graph_build.build_wallet_projection(G)

        cands = peeling_chain.detect(G, P)
        self.assertEqual(len(cands), 1)

        df = enrich_and_build_dataframe(cands, G)
        self.assertIn("decay_consistency_score", df.columns)
        self.assertAlmostEqual(df.loc[0, "decay_consistency_score"], cands[0].features["decay_consistency_score"], places=4)
        self.assertEqual(df.loc[0, "unique_ips"], 3)
        self.assertAlmostEqual(df.loc[0, "tor_vpn_fraction"], 2 / 3, places=4)


if __name__ == "__main__":
    unittest.main()
