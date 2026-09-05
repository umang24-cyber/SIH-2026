"""
detectors/layering.py — Fan-out / fan-in (layering) typology detector.

Algorithm summary
-----------------
1. Operate on the wallet-to-wallet MultiDiGraph projection (P) and full graph G.
2. Fan-out source detection:
     Find wallets whose UNIQUE out-neighbours (in P) >= min_fanout_degree.
3. For each fan-out source wallet S, collect recipients R = {R₁, … Rₙ}.
4. Reconvergence search (forward from each Rᵢ, up to max_reconvergence_hops):
     For each reachable wallet C from Rᵢ within the hop limit and satisfying:
       a. Temporal hop gap between consecutive steps <= max_hop_gap_seconds
       b. Total time span from fan-out <= max_time_window_seconds
     Record C as a potential convergence sink along with the contributing branch path.
5. Count how many Rᵢ wallets can reach each candidate sink C. A hit is when
     >= min_reconvergence_ratio of recipients reach the same C.
6. Time-window check: all transactions in the structure must fall within
     max_time_window_seconds.
7. Exchange filter: exclude C if its total transaction count in the full
     graph G exceeds exchange_degree_threshold (exchange-like hub).
8. Populate hop_sequence with detailed per-branch hop metadata for all contributing paths.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

import networkx as nx

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(
    G: nx.MultiDiGraph,
    P: nx.MultiDiGraph,
    *,
    min_fanout_degree: int = config.LAYER_MIN_FANOUT_DEGREE,
    max_reconvergence_hops: int = config.LAYER_MAX_RECONVERGENCE_HOPS,
    min_reconvergence_ratio: float = config.LAYER_MIN_RECONVERGENCE_RATIO,
    max_time_window_seconds: int = config.LAYER_MAX_TIME_WINDOW_SECONDS,
    max_hop_gap_seconds: int = config.LAYER_MAX_HOP_GAP_SECONDS,
    exchange_degree_threshold: int = config.LAYER_EXCHANGE_DEGREE_THRESHOLD,
    max_bfs_branching: int | None = None,
) -> list[CandidateStructure]:
    """
    Detect fan-out / fan-in (layering) candidate structures.

    Parameters
    ----------
    G : nx.MultiDiGraph
        Full heterogeneous graph.
    P : nx.MultiDiGraph
        Wallet-to-wallet projection.
    min_fanout_degree : int
        Minimum unique recipient wallets for fan-out source.
    max_reconvergence_hops : int
        Maximum hops to explore forward from each recipient.
    min_reconvergence_ratio : float
        Fraction of recipients that must reconverge at a single sink.
    max_time_window_seconds : int
        Maximum seconds spanning all transactions in the structure.
    max_hop_gap_seconds : int
        Maximum seconds allowed between consecutive hops along a branch.
    exchange_degree_threshold : int
        Maximum transaction participation count before a wallet is considered an exchange hub.
    max_bfs_branching : int | None
        Optional cap on out-edges explored per node during BFS.

    Returns
    -------
    list[CandidateStructure]
    """
    log.info("Layering detector: scanning wallet-projection for fan-out sources …")

    # Pre-compute per-wallet transaction count in the full graph
    # (used to filter out exchange-like hubs)
    wallet_tx_count = _compute_wallet_tx_count(G)

    # Build unique-successor view of P (ignoring parallel edges)
    out_neighbors: dict[str, set[str]] = {}
    for u, v in P.edges():
        out_neighbors.setdefault(u, set()).add(v)

    # Fan-out sources: wallets with unique out-degree >= threshold
    fanout_sources = [
        w for w, nbrs in out_neighbors.items()
        if len(nbrs) >= min_fanout_degree
    ]
    log.info("  %d fan-out source wallets found", len(fanout_sources))

    candidates: list[CandidateStructure] = []
    seen_structures: set[frozenset] = set()  # dedup by frozenset of member txids

    cid_counter = 0

    for source in fanout_sources:
        recipients = out_neighbors.get(source, set())
        total_recipients = len(recipients)
        if total_recipients == 0:
            continue

        # --- Reconvergence search ---
        # For each recipient, BFS forward up to max_reconvergence_hops with temporal checks
        # recipient_reach: recipient -> {sink_addr: branch_dict}
        recipient_reach: dict[str, dict[str, dict]] = {}
        for r in recipients:
            branches = _find_recipient_branches(
                source,
                r,
                P,
                wallet_tx_count=wallet_tx_count,
                max_hops=max_reconvergence_hops,
                max_hop_gap_seconds=max_hop_gap_seconds,
                max_time_window_seconds=max_time_window_seconds,
                exchange_degree_threshold=exchange_degree_threshold,
                max_bfs_branching=max_bfs_branching,
            )
            recipient_reach[r] = branches

        # Aggregate how many recipients reach each sink
        sink_counts: dict[str, int] = defaultdict(int)
        sink_branches_map: dict[str, dict[str, dict]] = defaultdict(dict)  # sink -> {recipient: branch_dict}

        for r, branches in recipient_reach.items():
            for sink, b_dict in branches.items():
                if sink == source:
                    continue  # ignore cycles back to source
                sink_counts[sink] += 1
                sink_branches_map[sink][r] = b_dict

        for sink, count in sink_counts.items():
            ratio = count / total_recipients
            if ratio < min_reconvergence_ratio:
                continue

            # Exchange filter
            if wallet_tx_count.get(sink, 0) > exchange_degree_threshold:
                log.debug("  Layering: sink %s filtered as exchange hub (%d txs)",
                          sink, wallet_tx_count.get(sink, 0))
                continue

            contributing_branches = sink_branches_map[sink]
            contributing_recipients = set(contributing_branches.keys())

            # Collect all txids involved in this layering candidate:
            # 1. Fan-out txids (source -> all recipients)
            # 2. Branch txids along all contributing paths to sink
            all_txids: set[int] = set()
            all_timestamps: list[datetime] = []

            for _, v, edata in P.out_edges(source, data=True):
                if v in recipients:
                    if edata.get("txid") is not None:
                        all_txids.add(edata["txid"])
                    if edata.get("timestamp"):
                        all_timestamps.append(edata["timestamp"])

            for r, b_info in contributing_branches.items():
                for txid in b_info.get("txids", []):
                    if txid is not None:
                        all_txids.add(txid)
                if b_info.get("first_timestamp"):
                    all_timestamps.append(b_info["first_timestamp"])
                if b_info.get("last_timestamp"):
                    all_timestamps.append(b_info["last_timestamp"])

            if not all_txids:
                continue

            # Time-window check across all participating transactions
            if all_timestamps:
                all_timestamps_sorted = sorted(all_timestamps)
                span_seconds = (
                    all_timestamps_sorted[-1] - all_timestamps_sorted[0]
                ).total_seconds()
                if span_seconds > max_time_window_seconds:
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

            # Collect all participating wallets
            all_intermediate_wallets: set[str] = set()
            for b_info in contributing_branches.values():
                all_intermediate_wallets.update(b_info.get("intermediate_wallets", []))

            all_wallets = (
                {source}
                | recipients
                | all_intermediate_wallets
                | {sink}
            )

            # Compute BTC moved and conservation ratio
            input_btc = sum(
                edata.get("amount_btc", 0.0)
                for _, v, edata in P.out_edges(source, data=True)
                if v in recipients
            )

            # Sum amount entering sink from contributing branches
            output_btc = sum(
                edata.get("amount_btc", 0.0)
                for u, _, edata in P.in_edges(sink, data=True)
                if u in all_intermediate_wallets or u in contributing_recipients
            )
            conservation_ratio = output_btc / input_btc if input_btc > 0 else 0.0

            # Build hop_sequence for all contributing branches (with clean wallet addresses)
            hop_seq = []
            for b_idx, (r, b_info) in enumerate(contributing_branches.items(), start=1):
                f_ts = b_info.get("first_timestamp")
                l_ts = b_info.get("last_timestamp")
                hop_seq.append({
                    "branch_id":            f"branch_{b_idx}",
                    "origin":               _clean_wallet(source),
                    "intermediate_wallets": [_clean_wallet(w) for w in b_info.get("intermediate_wallets", [])],
                    "sink":                 _clean_wallet(sink),
                    "txids":                b_info.get("txids", []),
                    "first_timestamp":      f_ts.isoformat() if f_ts else None,
                    "last_timestamp":       l_ts.isoformat() if l_ts else None,
                })

            candidates.append(CandidateStructure(
                candidate_id   = cid,
                candidate_type = "layering",
                member_txids   = sorted(all_txids),
                member_wallets = sorted({_clean_wallet(w) for w in all_wallets}),
                features       = {
                    "fan_out_degree":            len(recipients),
                    "fan_in_degree":             len(contributing_recipients),
                    "reconvergence_ratio":       round(ratio, 4),
                    "total_btc_moved":           round(input_btc, 8),
                    "amount_conservation_ratio": round(conservation_ratio, 6),
                    "time_span_seconds":         round(span_seconds, 1),
                    # network features filled by features.py
                    "avg_time_gap_seconds":      None,
                    "unique_ips":                None,
                    "unique_asns":               None,
                    "tor_vpn_fraction":          None,
                },
                hop_sequence = hop_seq,
            ))

    log.info("Layering detector: %d candidate structures found", len(candidates))
    return candidates


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_wallet(w: str) -> str:
    """Strip 'w:' prefix if present."""
    if w.startswith(config.PREFIX_WALLET):
        return w[len(config.PREFIX_WALLET):]
    return w


def _find_recipient_branches(
    source: str,
    recipient: str,
    P: nx.MultiDiGraph,
    wallet_tx_count: dict[str, int],
    *,
    max_hops: int,
    max_hop_gap_seconds: int,
    max_time_window_seconds: int,
    exchange_degree_threshold: int = config.LAYER_EXCHANGE_DEGREE_THRESHOLD,
    max_bfs_branching: int | None = None,
) -> dict[str, dict]:
    """
    Search forward from `recipient` up to `max_hops` in P to find reachable sinks.
    Enforces per-hop time gap <= max_hop_gap_seconds and total branch span <= max_time_window_seconds.
    Prunes traversal through exchange-hub wallets.

    Returns
    -------
    dict[str, dict]
        sink_wallet -> {
            "intermediate_wallets": list[str],
            "sink": str,
            "txids": list[int],
            "first_timestamp": datetime | None,
            "last_timestamp": datetime | None,
        }
    """
    fanout_edges = []
    if P.has_edge(source, recipient):
        for k, edata in P.get_edge_data(source, recipient).items():
            fanout_edges.append(edata)

    if fanout_edges:
        fanout_edges_sorted = sorted(
            fanout_edges,
            key=lambda e: e.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc)
        )
        fanout_txid = fanout_edges_sorted[0].get("txid")
        fanout_ts = fanout_edges_sorted[0].get("timestamp")
    else:
        fanout_txid = None
        fanout_ts = None

    initial_txids = [fanout_txid] if fanout_txid is not None else []

    # Queue item: (curr_wallet, hop_cnt, path_wallets, path_txids, first_ts, last_ts)
    queue = deque([
        (recipient, 0, [recipient], initial_txids, fanout_ts, fanout_ts)
    ])

    visited_at_hop: dict[str, int] = {recipient: 0}
    sink_branches: dict[str, dict] = {}

    while queue:
        curr, hop_cnt, path_wallets, path_txids, first_ts, last_ts = queue.popleft()

        if hop_cnt > 0 and curr != source and curr != recipient:
            if curr not in sink_branches:
                sink_branches[curr] = {
                    "intermediate_wallets": list(path_wallets[:-1]),
                    "sink": curr,
                    "txids": list(path_txids),
                    "first_timestamp": first_ts,
                    "last_timestamp": last_ts,
                }

        if hop_cnt >= max_hops:
            continue

        if not P.has_node(curr):
            continue

        # If curr is an exchange hub, do not traverse through it to downstream recipients
        if wallet_tx_count.get(curr, 0) > exchange_degree_threshold:
            continue

        out_edges_data = list(P.out_edges(curr, data=True))
        if max_bfs_branching is not None and len(out_edges_data) > max_bfs_branching:
            out_edges_data = out_edges_data[:max_bfs_branching]

        for _, nbr, edata in out_edges_data:
            if nbr == source or nbr in path_wallets:
                continue

            e_ts = edata.get("timestamp")
            e_txid = edata.get("txid")

            # Temporal validation
            if e_ts is not None and last_ts is not None:
                gap = (e_ts - last_ts).total_seconds()
                if gap < 0 or gap > max_hop_gap_seconds:
                    continue
            if e_ts is not None and first_ts is not None:
                span = (e_ts - first_ts).total_seconds()
                if span < 0 or span > max_time_window_seconds:
                    continue

            new_first_ts = first_ts if first_ts is not None else e_ts
            new_last_ts = e_ts if e_ts is not None else last_ts
            new_txids = path_txids + ([e_txid] if e_txid is not None else [])
            new_path_wallets = path_wallets + [nbr]

            if nbr in visited_at_hop and visited_at_hop[nbr] <= hop_cnt + 1:
                if nbr not in sink_branches and nbr != source and nbr != recipient:
                    sink_branches[nbr] = {
                        "intermediate_wallets": list(path_wallets),
                        "sink": nbr,
                        "txids": list(new_txids),
                        "first_timestamp": new_first_ts,
                        "last_timestamp": new_last_ts,
                    }
                continue

            visited_at_hop[nbr] = hop_cnt + 1
            queue.append((nbr, hop_cnt + 1, new_path_wallets, new_txids, new_first_ts, new_last_ts))

    return sink_branches


def _compute_wallet_tx_count(G: nx.MultiDiGraph) -> dict[str, int]:
    """
    Return a mapping of wallet address (and node_id) → number of transactions it participates
    in (sum of SENT + RECEIVED edge count in G).
    """
    counts: dict[str, int] = defaultdict(int)
    for src, dst, edata in G.edges(data=True):
        etype = edata.get("edge_type")
        if etype == "SENT":
            counts[src] += 1
            addr = G.nodes[src].get("address", "")
            if addr:
                counts[addr] += 1
        elif etype == "RECEIVED":
            counts[dst] += 1
            addr = G.nodes[dst].get("address", "")
            if addr:
                counts[addr] += 1
    return dict(counts)

