"""
detectors/layering.py — Fan-out / fan-in (layering) typology detector.

Algorithm summary
-----------------
1. Operate on the wallet-to-wallet MultiDiGraph projection (P).
2. Fan-out source detection:
     Find wallets whose UNIQUE out-neighbours (in P) ≥ LAYER_MIN_FANOUT_DEGREE.
3. For each fan-out source wallet S, collect recipients R = {R₁, … Rₙ}.
4. Reconvergence search (forward from each Rᵢ, up to LAYER_MAX_RECONVERGENCE_HOPS):
     For each reachable wallet C from Rᵢ within the hop limit, record C as
     a potential convergence sink.
5. Count how many Rᵢ wallets can reach each candidate sink C. A hit is when
     ≥ LAYER_MIN_RECONVERGENCE_RATIO of recipients reach the same C.
6. Time-window check: all transactions from the first fan-out to the last
     fan-in must fall within LAYER_MAX_TIME_WINDOW_SECONDS.
7. Exchange filter: exclude C if its total transaction count in the full
     graph G exceeds LAYER_EXCHANGE_DEGREE_THRESHOLD (exchange-like hub).
"""

from __future__ import annotations

import logging
from collections import defaultdict

import networkx as nx

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(
    G:  nx.DiGraph,
    P:  nx.MultiDiGraph,
) -> list[CandidateStructure]:
    """
    Detect fan-out / fan-in (layering) candidate structures.

    Parameters
    ----------
    G : nx.DiGraph
        Full heterogeneous graph.
    P : nx.MultiDiGraph
        Wallet-to-wallet projection.

    Returns
    -------
    list[CandidateStructure]
    """
    log.info("Layering detector: scanning wallet-projection for fan-out sources …")

    # Pre-compute per-wallet transaction count in the full graph
    # (used to filter out exchange-like hubs)
    wallet_tx_count = _compute_wallet_tx_count(G)

    # Build unique-successor view of P (ignoring parallel edges)
    # out_neighbors[w] = set of wallets that w transfers to (any amount, any tx)
    out_neighbors: dict[str, set[str]] = {}
    in_neighbors:  dict[str, set[str]] = {}
    for u, v in P.edges():
        out_neighbors.setdefault(u, set()).add(v)
        in_neighbors.setdefault(v, set()).add(u)

    # Fan-out sources: wallets with unique out-degree >= threshold
    fanout_sources = [
        w for w, nbrs in out_neighbors.items()
        if len(nbrs) >= config.LAYER_MIN_FANOUT_DEGREE
    ]
    log.info("  %d fan-out source wallets found", len(fanout_sources))

    candidates: list[CandidateStructure] = []
    seen_structures: set[frozenset] = set()  # dedup by frozenset of member txids

    cid_counter = 0

    for source in fanout_sources:
        recipients = out_neighbors.get(source, set())

        # --- Collect all txids in the fan-out stage ---
        fanout_txids: set[int] = set()
        fanout_timestamps = []
        for _, v, edata in P.out_edges(source, data=True):
            if v in recipients:
                if edata.get("txid") is not None:
                    fanout_txids.add(edata["txid"])
                    if edata.get("timestamp"):
                        fanout_timestamps.append(edata["timestamp"])

        # --- Reconvergence search ---
        # For each recipient, BFS forward up to LAYER_MAX_RECONVERGENCE_HOPS
        # Record which candidates each recipient can reach
        recipient_reach: dict[str, set[str]] = {}
        for r in recipients:
            reachable = _bfs_forward(r, out_neighbors, config.LAYER_MAX_RECONVERGENCE_HOPS)
            recipient_reach[r] = reachable

        # Count how many recipients reach each candidate sink
        sink_counts: dict[str, int] = defaultdict(int)
        sink_contributors: dict[str, set[str]] = defaultdict(set)
        for r, reachable in recipient_reach.items():
            for sink in reachable:
                if sink == source:
                    continue  # ignore self
                sink_counts[sink] += 1
                sink_contributors[sink].add(r)

        total_recipients = len(recipients)
        if total_recipients == 0:
            continue

        for sink, count in sink_counts.items():
            ratio = count / total_recipients
            if ratio < config.LAYER_MIN_RECONVERGENCE_RATIO:
                continue

            # Exchange filter
            if wallet_tx_count.get(sink, 0) > config.LAYER_EXCHANGE_DEGREE_THRESHOLD:
                log.debug("  Layering: sink %s filtered as exchange hub (%d txs)",
                          sink, wallet_tx_count.get(sink, 0))
                continue

            # Collect all txids in the fan-in stage (contributing recipients → sink)
            fanin_txids: set[int] = set()
            fanin_timestamps = []
            contributing = sink_contributors[sink]
            for u, _, edata in P.in_edges(sink, data=True):
                if u in contributing:
                    if edata.get("txid") is not None:
                        fanin_txids.add(edata["txid"])
                    if edata.get("timestamp"):
                        fanin_timestamps.append(edata["timestamp"])

            all_txids = fanout_txids | fanin_txids
            if not all_txids:
                continue

            # Time-window check
            all_timestamps = fanout_timestamps + fanin_timestamps
            if all_timestamps:
                all_timestamps_sorted = sorted(all_timestamps)
                span_seconds = (
                    all_timestamps_sorted[-1] - all_timestamps_sorted[0]
                ).total_seconds()
                if span_seconds > config.LAYER_MAX_TIME_WINDOW_SECONDS:
                    continue
            else:
                span_seconds = 0.0

            # Dedup by frozen txid set
            key = frozenset(all_txids)
            if key in seen_structures:
                continue
            seen_structures.add(key)

            cid_counter += 1
            cid = f"layer_{cid_counter:04d}"

            all_wallets = (
                {source}
                | recipients
                | contributing
                | {sink}
            )

            # Compute total BTC moved through the structure
            total_btc = sum(
                edata.get("amount_btc", 0.0)
                for _, v, edata in P.out_edges(source, data=True)
                if v in recipients
            )

            # Amount conservation ratio: output_btc / input_btc
            input_btc  = sum(
                edata.get("amount_btc", 0.0)
                for _, v, edata in P.out_edges(source, data=True)
                if v in recipients
            )
            output_btc = sum(
                edata.get("amount_btc", 0.0)
                for u, _, edata in P.in_edges(sink, data=True)
                if u in contributing
            )
            conservation_ratio = output_btc / input_btc if input_btc > 0 else 0.0

            candidates.append(CandidateStructure(
                candidate_id   = cid,
                candidate_type = "layering",
                member_txids   = sorted(all_txids),
                member_wallets = sorted(all_wallets),
                features       = {
                    "fan_out_degree":          len(recipients),
                    "fan_in_degree":           len(contributing),
                    "reconvergence_ratio":     round(ratio, 4),
                    "total_btc_moved":         round(total_btc, 8),
                    "amount_conservation_ratio": round(conservation_ratio, 6),
                    "time_span_seconds":       round(span_seconds, 1),
                    # network features filled by features.py
                    "avg_time_gap_seconds":    None,
                    "unique_ips":              None,
                    "unique_asns":             None,
                    "tor_vpn_fraction":        None,
                },
                hop_sequence = None,
            ))

    log.info("Layering detector: %d candidate structures found", len(candidates))
    return candidates


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _bfs_forward(
    start:         str,
    out_neighbors: dict[str, set[str]],
    max_hops:      int,
) -> set[str]:
    """BFS from ``start`` up to ``max_hops`` steps; return all reachable wallets."""
    visited = set()
    frontier = {start}
    for _ in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for nbr in out_neighbors.get(node, set()):
                if nbr not in visited and nbr != start:
                    next_frontier.add(nbr)
                    visited.add(nbr)
        frontier = next_frontier
        if not frontier:
            break
    return visited


def _compute_wallet_tx_count(G: nx.DiGraph) -> dict[str, int]:
    """
    Return a mapping of wallet address → number of transactions it participates
    in (sum of SENT + RECEIVED edge count in G).
    """
    counts: dict[str, int] = defaultdict(int)
    for src, dst, edata in G.edges(data=True):
        etype = edata.get("edge_type")
        if etype == "SENT":
            addr = G.nodes[src].get("address", "")
            if addr:
                counts[addr] += 1
        elif etype == "RECEIVED":
            addr = G.nodes[dst].get("address", "")
            if addr:
                counts[addr] += 1
    return dict(counts)
