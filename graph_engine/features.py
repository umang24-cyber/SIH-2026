"""
features.py — Enrich CandidateStructure objects with network-layer features
and produce the final ML-handoff DataFrame.

After typology detectors run and populate member_txids / member_wallets,
this module:

1. Looks up each member txid in the full graph G to find BROADCAST edges
   (IP nodes) and collects relay_ip, asn, node_type_infra.
2. Computes:
     unique_ips        — distinct relay IPs broadcasting any member tx
     unique_asns       — distinct ASNs
     tor_vpn_fraction  — fraction of member txids broadcast from suspicious infra
3. Writes the enriched features back into candidate.features (in-place).
4. Returns a flat pandas DataFrame suitable for ML handoff.
"""

from __future__ import annotations

import logging

import networkx as nx
import pandas as pd

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enrich_and_build_dataframe(
    candidates: list[CandidateStructure],
    G: nx.MultiDiGraph,
) -> pd.DataFrame:
    """
    Enrich every candidate with network-layer features and return a flat DataFrame.

    Parameters
    ----------
    candidates : list[CandidateStructure]
        All detected candidates (peeling, layering, mixing combined).
    G : nx.MultiDiGraph
        Full heterogeneous graph (needed to resolve BROADCAST edges for IPs).

    Returns
    -------
    pd.DataFrame
        One row per candidate, all feature columns present.
        Columns that don't apply to a given typology are NaN.
    """
    # Build txid → IP info index once
    tx_ip_index = _build_tx_ip_index(G)

    for cand in candidates:
        _enrich_network_features(cand, tx_ip_index)
        _enrich_member_ips(cand, tx_ip_index)

    log.info(
        "Feature enrichment complete: %d candidates (peel=%d, layer=%d, mix=%d)",
        len(candidates),
        sum(1 for c in candidates if c.candidate_type == "peeling_chain"),
        sum(1 for c in candidates if c.candidate_type == "layering"),
        sum(1 for c in candidates if c.candidate_type == "mixing"),
    )

    return _to_dataframe(candidates)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_tx_ip_index(G: nx.MultiDiGraph) -> dict[int, dict]:
    """
    Return a mapping txid (int) → {
        relay_ip:        str,
        asn:             str,
        node_type_infra: str,   # residential / datacenter / tor_exit_node / …
    }
    """
    index: dict[int, dict] = {}
    for src, dst, edata in G.edges(data=True):
        if edata.get("edge_type") != "BROADCAST":
            continue
        txid = G.nodes[dst].get("txid")
        if txid is None:
            continue
        ip_data = G.nodes[src]
        index[txid] = {
            "relay_ip":        ip_data.get("relay_ip", ""),
            "asn":             ip_data.get("asn", ""),
            "node_type_infra": ip_data.get("node_type_infra", ""),
        }
    return index


def _enrich_network_features(
    cand: CandidateStructure,
    tx_ip_index: dict[int, dict],
) -> None:
    """Fill unique_ips, unique_asns, tor_vpn_fraction into cand.features in-place."""
    ips:   set[str] = set()
    asns:  set[str] = set()
    n_suspicious = 0

    for txid in cand.member_txids:
        info = tx_ip_index.get(txid)
        if not info:
            continue
        ips.add(info["relay_ip"])
        asns.add(info["asn"])
        if info["node_type_infra"] in config.SUSPICIOUS_NODE_TYPES:
            n_suspicious += 1

    total = len(cand.member_txids)
    tor_frac = n_suspicious / total if total > 0 else 0.0

    cand.features["unique_ips"]         = len(ips)
    cand.features["unique_asns"]        = len(asns)
    cand.features["tor_vpn_fraction"]   = round(tor_frac, 6)


def _enrich_member_ips(
    cand: CandidateStructure,
    tx_ip_index: dict[int, dict],
) -> None:
    """Populate cand.member_ips with the unique relay IPs for all member txids."""
    ips: set[str] = set()
    for txid in cand.member_txids:
        info = tx_ip_index.get(txid)
        if info and info["relay_ip"]:
            ips.add(info["relay_ip"])
    cand.member_ips = sorted(ips)


# Column order for the ML-handoff CSV
_COMMON_COLS = [
    "candidate_id",
    "candidate_type",
    "member_txids",
    "member_wallets",
    "total_btc_moved",
    "time_span_seconds",
    "unique_ips",
    "unique_asns",
    "tor_vpn_fraction",
]
_PEEL_COLS = [
    "chain_length",
    "total_peeled_btc",
    "amount_decay_rate",
    "decay_consistency_score",
    "avg_time_gap_seconds",
    "min_time_gap_seconds",
    "max_time_gap_seconds",
]
_LAYER_COLS = [
    "fan_out_degree",
    "fan_in_degree",
    "reconvergence_ratio",
    "amount_conservation_ratio",
    "avg_time_gap_seconds",
]
_MIX_COLS = [
    "cluster_size",
    "cluster_density",
    "external_connectivity_ratio",
    "num_rounds",
    "output_amount_cv",
    "avg_output_btc",
]

_ALL_FEATURE_COLS = list(dict.fromkeys(
    _COMMON_COLS + _PEEL_COLS + _LAYER_COLS + _MIX_COLS
))


def _to_dataframe(candidates: list[CandidateStructure]) -> pd.DataFrame:
    rows = []
    for cand in candidates:
        row: dict = {
            "candidate_id":  cand.candidate_id,
            "candidate_type": cand.candidate_type,
            "member_txids":  str(cand.member_txids),
            "member_wallets": str(cand.member_wallets),
        }
        row.update(cand.features)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Ensure all expected columns exist (NaN for missing ones)
    for col in _ALL_FEATURE_COLS:
        if col not in df.columns:
            df[col] = float("nan")

    # Re-order columns: defined list first, then any extras
    ordered = [c for c in _ALL_FEATURE_COLS if c in df.columns]
    extras  = [c for c in df.columns if c not in _ALL_FEATURE_COLS]
    df = df[ordered + extras]

    return df.reset_index(drop=True)
