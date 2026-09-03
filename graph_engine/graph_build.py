"""
graph_build.py — Construct the heterogeneous directed graph and wallet projection.

Exports
-------
build_full_graph(df) → networkx.DiGraph
    Heterogeneous graph with three node types (wallet, transaction, ip)
    and three edge types (SENT, RECEIVED, BROADCAST).

build_wallet_projection(G) → networkx.DiGraph
    Wallet-to-wallet transfer graph derived from the full graph.
    A directed edge w:A → w:B exists for each path w:A → tx:T → w:B,
    with attributes: txid, amount_btc (B's output amount), timestamp.

Both graphs are the canonical inputs to the typology detectors.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import networkx as nx
import pandas as pd

from graph_engine import config

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_full_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Build the heterogeneous directed graph from the merged DataFrame.

    Node attribute ``node_type`` discriminates wallet / transaction / ip nodes.
    Edge attribute ``edge_type`` discriminates SENT / RECEIVED / BROADCAST edges.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``ingest.load_merged_df()``.

    Returns
    -------
    nx.DiGraph
    """
    G = nx.DiGraph()

    log.info("Building full heterogeneous graph from %d transactions …", len(df))

    for row in df.itertuples(index=False):
        tx_id  = f"{config.PREFIX_TX}{row.txid}"
        ip_id  = f"{config.PREFIX_IP}{row.relay_ip}"

        # ------------------------------------------------------------------
        # Transaction node
        # ------------------------------------------------------------------
        ts = row.timestamp
        # Ensure we store ISO strings (JSON-serialisable) alongside the raw ts
        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

        G.add_node(
            tx_id,
            node_type    = "transaction",
            txid         = int(row.txid),
            timestamp    = ts,
            timestamp_iso= ts_iso,
            fee_btc      = float(row.fee_btc),
            script_type  = str(row.script_type),
            scenario_id  = str(row.scenario_id),
            split        = str(row.split),
            num_inputs   = len(row.input_addresses),
            num_outputs  = len(row.output_addresses),
            total_input_btc  = float(sum(row.input_amounts)),
            total_output_btc = float(sum(row.output_amounts)),
        )

        # ------------------------------------------------------------------
        # IP node  (idempotent — first occurrence wins for static attributes)
        # ------------------------------------------------------------------
        relay_ts     = row.relay_timestamp
        relay_ts_iso = relay_ts.isoformat() if hasattr(relay_ts, "isoformat") else str(relay_ts)

        if ip_id not in G:
            G.add_node(
                ip_id,
                node_type       = "ip",
                relay_ip        = str(row.relay_ip),
                country_code    = str(row.country_code),
                asn             = str(row.asn),
                isp             = str(row.isp),
                node_type_infra = str(row.node_type),  # renamed to avoid collision
                relay_port      = int(row.relay_port),
            )

        # BROADCAST edge: IP → Transaction
        G.add_edge(
            ip_id, tx_id,
            edge_type       = "BROADCAST",
            relay_timestamp = relay_ts,
            relay_timestamp_iso = relay_ts_iso,
            relay_port      = int(row.relay_port),
            user_agent      = str(row.user_agent),
        )

        # ------------------------------------------------------------------
        # Wallet nodes + SENT edges  (input side)
        # ------------------------------------------------------------------
        for addr, amt in zip(row.input_addresses, row.input_amounts):
            w_id = f"{config.PREFIX_WALLET}{addr}"
            if w_id not in G:
                G.add_node(w_id, node_type="wallet", address=str(addr))
            # SENT: Wallet → Transaction
            G.add_edge(
                w_id, tx_id,
                edge_type  = "SENT",
                amount_btc = float(amt),
            )

        # ------------------------------------------------------------------
        # Wallet nodes + RECEIVED edges  (output side)
        # ------------------------------------------------------------------
        for addr, amt in zip(row.output_addresses, row.output_amounts):
            w_id = f"{config.PREFIX_WALLET}{addr}"
            if w_id not in G:
                G.add_node(w_id, node_type="wallet", address=str(addr))
            # RECEIVED: Transaction → Wallet
            G.add_edge(
                tx_id, w_id,
                edge_type  = "RECEIVED",
                amount_btc = float(amt),
            )

    _log_graph_stats(G)
    return G


def build_wallet_projection(G: nx.DiGraph) -> nx.DiGraph:
    """
    Build the wallet-to-wallet transfer graph from the full heterogeneous graph.

    For each path  w:A -[SENT]→ tx:T -[RECEIVED]→ w:B  in G, add a directed
    edge  w:A → w:B  in the projection carrying:
        txid        : int
        amount_btc  : float  (the RECEIVED amount for B in that tx)
        timestamp   : datetime  (block timestamp of tx:T)

    Multiple transfers between the same pair of wallets produce multiple
    parallel edges — we use a MultiDiGraph for the projection so that timing
    and amounts are never collapsed.

    Returns
    -------
    nx.MultiDiGraph
        Wallet-to-wallet transfer graph preserving per-transaction granularity.
    """
    log.info("Building wallet-to-wallet projection …")
    P = nx.MultiDiGraph()

    for tx_id, tx_data in G.nodes(data=True):
        if tx_data.get("node_type") != "transaction":
            continue

        # Wallets that sent to this transaction
        senders = [
            (nbr, G[nbr][tx_id]["amount_btc"])
            for nbr in G.predecessors(tx_id)
            if G.nodes[nbr].get("node_type") == "wallet"
        ]

        # Wallets that received from this transaction
        receivers = [
            (nbr, G[tx_id][nbr]["amount_btc"])
            for nbr in G.successors(tx_id)
            if G.nodes[nbr].get("node_type") == "wallet"
        ]

        if not senders or not receivers:
            continue

        ts  = tx_data["timestamp"]
        txid = tx_data["txid"]

        # Ensure wallet nodes exist in projection
        for w, _ in senders + receivers:
            if w not in P:
                P.add_node(w, **G.nodes[w])

        # Add one edge per (sender, receiver) pair per transaction
        for s_addr, _s_amt in senders:
            for r_addr, r_amt in receivers:
                if s_addr == r_addr:
                    # Skip self-loops (change back to same wallet is possible
                    # but we don't want trivial self-edges polluting traversals)
                    continue
                P.add_edge(
                    s_addr, r_addr,
                    txid       = txid,
                    amount_btc = float(r_amt),
                    timestamp  = ts,
                )

    log.info(
        "Wallet projection: %d wallet nodes, %d transfer edges",
        P.number_of_nodes(),
        P.number_of_edges(),
    )
    return P


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _log_graph_stats(G: nx.DiGraph) -> None:
    node_types = {}
    edge_types = {}

    for _, data in G.nodes(data=True):
        nt = data.get("node_type", "unknown")
        node_types[nt] = node_types.get(nt, 0) + 1

    for _, _, data in G.edges(data=True):
        et = data.get("edge_type", "unknown")
        edge_types[et] = edge_types.get(et, 0) + 1

    log.info(
        "Full graph built: %d nodes %s | %d edges %s",
        G.number_of_nodes(), node_types,
        G.number_of_edges(), edge_types,
    )
