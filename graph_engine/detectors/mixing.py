"""
detectors/mixing.py — Mixing-cluster (CoinJoin-like) typology detector.

Algorithm summary
-----------------
1. Build a time-windowed undirected wallet co-participation graph (CP):
     For each transaction with ≥ MIX_MIN_INPUTS inputs AND ≥ MIX_MIN_OUTPUTS
     outputs, add undirected edges between all pairs of input wallets
     (they co-sign the CoinJoin-like transaction together).
2. Run Louvain community detection on CP.
3. For each community of size ≥ MIX_MIN_COMMUNITY_SIZE:
     a. Internal density = edges_within / (n*(n-1)/2)
     b. External connectivity ratio = edges_crossing / total_edges
     c. Output amount CV = std(output amounts) / mean(output amounts)
     d. Time window = span of all member transaction timestamps
4. Accept communities that satisfy all four filters.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict

import networkx as nx

try:
    import community as community_louvain   # python-louvain package
except ImportError:
    community_louvain = None  # handled gracefully below

from graph_engine import config
from graph_engine.structures import CandidateStructure

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect(
    G: nx.DiGraph,
    P: nx.MultiDiGraph,
) -> list[CandidateStructure]:
    """
    Detect mixing-cluster candidate structures using Louvain community detection.

    Parameters
    ----------
    G : nx.DiGraph
        Full heterogeneous graph.
    P : nx.MultiDiGraph
        Wallet-to-wallet projection (not used directly here, but kept for
        consistent interface with other detectors).

    Returns
    -------
    list[CandidateStructure]
    """
    if community_louvain is None:
        log.error(
            "python-louvain is not installed. Run: pip install python-louvain. "
            "Mixing detector disabled."
        )
        return []

    log.info("Mixing detector: building co-participation graph …")

    # ------------------------------------------------------------------
    # Step 1: Build the co-participation graph
    # ------------------------------------------------------------------
    CP = nx.Graph()

    # tx_meta[txid] = {output_amounts, timestamp}
    tx_meta: dict[int, dict] = {}

    for tx_id, tx_data in G.nodes(data=True):
        if tx_data.get("node_type") != "transaction":
            continue

        txid = tx_data["txid"]
        num_in  = tx_data.get("num_inputs", 0)
        num_out = tx_data.get("num_outputs", 0)

        if num_in < config.MIX_MIN_INPUTS or num_out < config.MIX_MIN_OUTPUTS:
            continue

        # Collect input wallets
        input_wallets = [
            nbr for nbr in G.predecessors(tx_id)
            if G.nodes[nbr].get("node_type") == "wallet"
        ]
        # Collect output amounts for CV computation
        output_amounts = [
            G[tx_id][nbr]["amount_btc"]
            for nbr in G.successors(tx_id)
            if G.nodes[nbr].get("node_type") == "wallet"
        ]

        tx_meta[txid] = {
            "output_amounts": output_amounts,
            "timestamp":      tx_data.get("timestamp"),
        }

        # Add co-participation edges for every pair of input wallets
        for i in range(len(input_wallets)):
            for j in range(i + 1, len(input_wallets)):
                u, v = input_wallets[i], input_wallets[j]
                # Accumulate co-participation count as edge weight
                if CP.has_edge(u, v):
                    CP[u][v]["weight"] += 1
                else:
                    CP.add_edge(u, v, weight=1, txids=set())
                CP[u][v].setdefault("txids", set()).add(txid)

    log.info(
        "  Co-participation graph: %d nodes, %d edges",
        CP.number_of_nodes(), CP.number_of_edges(),
    )

    if CP.number_of_nodes() < config.MIX_MIN_COMMUNITY_SIZE:
        log.info("  Co-participation graph too small — no mixing candidates.")
        return []

    # ------------------------------------------------------------------
    # Step 2: Louvain community detection
    # ------------------------------------------------------------------
    partition: dict[str, int] = community_louvain.best_partition(
        CP,
        weight="weight",
        random_state=config.LOUVAIN_RANDOM_STATE,
    )

    # Group wallets by community ID
    communities: dict[int, list[str]] = defaultdict(list)
    for wallet, comm_id in partition.items():
        communities[comm_id].append(wallet)

    log.info("  Louvain found %d communities", len(communities))

    # ------------------------------------------------------------------
    # Step 3 & 4: Filter communities
    # ------------------------------------------------------------------
    candidates: list[CandidateStructure] = []
    cid_counter = 0

    for comm_id, wallets in communities.items():
        n = len(wallets)
        if n < config.MIX_MIN_COMMUNITY_SIZE:
            continue

        wallet_set = set(wallets)

        # --- Internal density ---
        subgraph = CP.subgraph(wallet_set)
        internal_edges = subgraph.number_of_edges()
        max_possible = n * (n - 1) / 2
        density = internal_edges / max_possible if max_possible > 0 else 0.0
        if density < config.MIX_MIN_DENSITY:
            continue

        # --- External connectivity ratio ---
        deg_sum = sum(d for _, d in CP.degree(wallet_set))
        total_edges_incident = deg_sum - internal_edges
        external_edges = total_edges_incident - internal_edges
        ext_ratio = (
            external_edges / total_edges_incident
            if total_edges_incident > 0 else 0.0
        )
        if ext_ratio > config.MIX_MAX_EXTERNAL_RATIO:
            continue

        # --- Collect member txids and timestamps ---
        member_txids: set[int] = set()
        for _, _, edata in subgraph.edges(data=True):
            member_txids |= edata.get("txids", set())

        # --- Time window check ---
        timestamps = [
            tx_meta[tid]["timestamp"]
            for tid in member_txids
            if tid in tx_meta and tx_meta[tid]["timestamp"] is not None
        ]
        if not timestamps:
            continue
        ts_sorted = sorted(timestamps)
        span_seconds = (ts_sorted[-1] - ts_sorted[0]).total_seconds()
        if span_seconds > config.MIX_MAX_TIME_WINDOW_SECONDS:
            continue

        # --- Output amount CV ---
        all_output_amounts = []
        for tid in member_txids:
            if tid in tx_meta:
                all_output_amounts.extend(tx_meta[tid]["output_amounts"])

        if len(all_output_amounts) < 2:
            continue
        mean_amt = statistics.mean(all_output_amounts)
        if mean_amt == 0:
            continue
        stdev_amt = statistics.stdev(all_output_amounts)
        cv = stdev_amt / mean_amt
        if cv > config.MIX_MAX_AMOUNT_CV:
            continue

        # --- Passed all filters — build candidate ---
        cid_counter += 1
        cid = f"mix_{cid_counter:04d}"

        # Estimate mixing rounds as max hop depth within the community subgraph
        subgraph = CP.subgraph(wallet_set)
        try:
            diameter = nx.diameter(subgraph) if nx.is_connected(subgraph) else 0
        except nx.exception.NetworkXError:
            diameter = 0

        candidates.append(CandidateStructure(
            candidate_id   = cid,
            candidate_type = "mixing",
            member_txids   = sorted(member_txids),
            member_wallets = sorted(wallet_set),
            features       = {
                "cluster_size":               n,
                "cluster_density":            round(density, 6),
                "external_connectivity_ratio": round(ext_ratio, 6),
                "num_rounds":                 diameter,
                "output_amount_cv":           round(cv, 6),
                "avg_output_btc":             round(mean_amt, 8),
                "total_btc_moved":            round(sum(all_output_amounts), 8),
                "time_span_seconds":          round(span_seconds, 1),
                # network features filled by features.py
                "unique_ips":                 None,
                "unique_asns":               None,
                "tor_vpn_fraction":           None,
            },
            hop_sequence = None,
        ))

    log.info("Mixing detector: %d candidate clusters found", len(candidates))
    return candidates
