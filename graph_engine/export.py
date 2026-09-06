"""
export.py — Produce the two output artefacts:

1. graph_export.json   — Dashboard-ready JSON for the frontend visualiser.
                         Schema is locked (documented in GRAPH_EXPORT_SCHEMA.md).
2. candidates_ml_handoff.csv — Flat feature-vector table for the ML engineer.

IMPORTANT — FRONTEND CONTRACT
------------------------------
The field names below are LOCKED once any downstream consumer builds against
them. Do not rename fields without coordinating a schema version bump.
All datetime strings are ISO-8601 UTC (Z suffix).
All amounts are floats in BTC.
candidate_ids on nodes/edges is the join key for highlight/filter in the UI.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import networkx as nx
import pandas as pd

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_graph_json(
    G:          nx.DiGraph,
    candidates: list[CandidateStructure],
    output_path: Path = config.GRAPH_EXPORT_JSON,
) -> None:
    """
    Write the full graph + candidate annotations to ``output_path`` as JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Building graph_export.json …")

    # Pre-build: for each node/edge id, which candidate_ids reference it?
    node_to_cands:  dict[str, list[str]] = {}
    edge_to_cands:  dict[tuple, list[str]] = {}

    for cand in candidates:
        for txid in cand.member_txids:
            node_id = f"{config.PREFIX_TX}{txid}"
            node_to_cands.setdefault(node_id, []).append(cand.candidate_id)
        for wallet in cand.member_wallets:
            node_id = f"{config.PREFIX_WALLET}{wallet}"
            node_to_cands.setdefault(node_id, []).append(cand.candidate_id)
        for ip in cand.member_ips:
            node_id = f"{config.PREFIX_IP}{ip}"
            node_to_cands.setdefault(node_id, []).append(cand.candidate_id)

    # We tag edges by their endpoint pair (source, target).
    # For edges whose both endpoints belong to the same candidate, tag them.
    cand_tx_sets: dict[str, set[int]] = {
        c.candidate_id: set(c.member_txids) for c in candidates
    }
    cand_wallet_sets: dict[str, set[str]] = {
        c.candidate_id: set(c.member_wallets) for c in candidates
    }

    # ---------------------------------------------------------------------------
    # Serialise nodes
    # ---------------------------------------------------------------------------
    nodes_out = []
    for node_id, data in G.nodes(data=True):
        ntype = data.get("node_type")
        cids  = list(dict.fromkeys(node_to_cands.get(node_id, [])))

        if ntype == "wallet":
            nodes_out.append({
                "id":           node_id,
                "node_type":    "wallet",
                "address":      data.get("address", ""),
                "degree_in":    G.in_degree(node_id),
                "degree_out":   G.out_degree(node_id),
                "candidate_ids": cids,
            })

        elif ntype == "transaction":
            ts = data.get("timestamp_iso") or _ts_iso(data.get("timestamp"))
            nodes_out.append({
                "id":                node_id,
                "node_type":         "transaction",
                "txid":              data.get("txid"),
                "timestamp":         ts,
                "fee_btc":           data.get("fee_btc"),
                "script_type":       data.get("script_type"),
                "scenario_id":       data.get("scenario_id"),
                "total_input_btc":   data.get("total_input_btc"),
                "total_output_btc":  data.get("total_output_btc"),
                "num_inputs":        data.get("num_inputs"),
                "num_outputs":       data.get("num_outputs"),
                "candidate_ids":     cids,
            })

        elif ntype == "ip":
            nodes_out.append({
                "id":              node_id,
                "node_type":       "ip",
                "relay_ip":        data.get("relay_ip", ""),
                "country_code":    data.get("country_code", ""),
                "asn":             data.get("asn", ""),
                "isp":             data.get("isp", ""),
                "node_type_infra": data.get("node_type_infra", ""),
                "relay_port":      data.get("relay_port"),
                "candidate_ids":   cids,
            })

    # ---------------------------------------------------------------------------
    # Serialise edges
    # ---------------------------------------------------------------------------
    edges_out = []
    for src, dst, edata in G.edges(data=True):
        etype = edata.get("edge_type")

        # Determine candidate membership
        src_c = node_to_cands.get(src, []) if not src.startswith(config.PREFIX_IP) else []
        dst_c = node_to_cands.get(dst, []) if not dst.startswith(config.PREFIX_IP) else []
        cids = list(dict.fromkeys(src_c + dst_c))

        if etype == "SENT":
            edges_out.append({
                "source":      src,
                "target":      dst,
                "edge_type":   "SENT",
                "amount_btc":  edata.get("amount_btc"),
                "candidate_ids": cids,
            })
        elif etype == "RECEIVED":
            edges_out.append({
                "source":      src,
                "target":      dst,
                "edge_type":   "RECEIVED",
                "amount_btc":  edata.get("amount_btc"),
                "candidate_ids": cids,
            })
        elif etype == "BROADCAST":
            rts = edata.get("relay_timestamp_iso") or _ts_iso(edata.get("relay_timestamp"))
            edges_out.append({
                "source":           src,
                "target":           dst,
                "edge_type":        "BROADCAST",
                "relay_timestamp":  rts,
                "relay_port":       edata.get("relay_port"),
                "user_agent":       edata.get("user_agent", ""),
                "candidate_ids":    cids,
            })

    # ---------------------------------------------------------------------------
    # Serialise candidates
    # ---------------------------------------------------------------------------
    candidates_out = []
    for cand in candidates:
        candidates_out.append({
            "candidate_id":   cand.candidate_id,
            "candidate_type": cand.candidate_type,
            "member_txids":   cand.member_txids,
            "member_wallets": cand.member_wallets,
            "member_ips":     cand.member_ips,
            "features":       cand.features,
            "hop_sequence":   cand.hop_sequence,
        })

    # ---------------------------------------------------------------------------
    # Assemble and write
    # ---------------------------------------------------------------------------
    export = {
        "metadata": {
            "schema_version":  "1.0",
            "generated_at":    _now_iso(),
            "total_nodes":     len(nodes_out),
            "total_edges":     len(edges_out),
            "total_candidates": len(candidates_out),
            "candidate_counts": {
                "peeling_chain": sum(1 for c in candidates if c.candidate_type == "peeling_chain"),
                "layering":      sum(1 for c in candidates if c.candidate_type == "layering"),
                "mixing":        sum(1 for c in candidates if c.candidate_type == "mixing"),
            },
        },
        "nodes":      nodes_out,
        "edges":      edges_out,
        "candidates": candidates_out,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, default=_json_default, indent=2)

    size_mb = output_path.stat().st_size / 1_048_576
    log.info(
        "graph_export.json written: %d nodes, %d edges, %d candidates (%.1f MB)",
        len(nodes_out), len(edges_out), len(candidates_out), size_mb,
    )


def export_ml_handoff_csv(
    df: pd.DataFrame,
    output_path: Path = config.ML_HANDOFF_CSV,
) -> None:
    """
    Write the flat candidates feature-vector table to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(
        "candidates_ml_handoff.csv written: %d candidates, %d columns",
        len(df), len(df.columns),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ts_iso(ts) -> str | None:
    if ts is None:
        return None
    if hasattr(ts, "isoformat"):
        return ts.isoformat()
    return str(ts)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _json_default(obj):
    """Fallback JSON serialiser for types json.dumps doesn't handle."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "item"):   # numpy scalar
        return obj.item()
    return str(obj)


def _edge_candidate_ids(
    src: str,
    dst: str,
    etype: str | None,
    cand_tx_sets: dict[str, set[int]],
    cand_wallet_sets: dict[str, set[str]],
    candidates: list[CandidateStructure],
) -> list[str]:
    """
    Return candidate_ids whose member sets include BOTH endpoints of this edge.
    """
    cids = []
    for cand in candidates:
        tx_set  = cand_tx_sets[cand.candidate_id]
        w_set   = cand_wallet_sets[cand.candidate_id]

        def _in(node_id: str) -> bool:
            if node_id.startswith(config.PREFIX_TX):
                try:
                    return int(node_id[len(config.PREFIX_TX):]) in tx_set
                except ValueError:
                    return False
            if node_id.startswith(config.PREFIX_WALLET):
                return node_id[len(config.PREFIX_WALLET):] in w_set
            return False  # IP nodes intentionally not included in edge tags

        if _in(src) or _in(dst):
            cids.append(cand.candidate_id)

    return list(dict.fromkeys(cids))
