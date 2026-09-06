"""
graph_build.py — Construct the heterogeneous directed graph and wallet projection.

Exports
-------
build_full_graph(df) → networkx.MultiDiGraph
    Heterogeneous graph with three node types (wallet, transaction, ip)
    and three edge types (SENT, RECEIVED, BROADCAST).

build_full_graph_from_records(records) → networkx.MultiDiGraph
    Same graph, constructed from an iterable of RawTxRecord objects
    (see ingest.iter_records).  This is the schema-decoupled path.

build_wallet_projection(G) → networkx.MultiDiGraph
    Wallet-to-wallet transfer graph derived from the full graph.
    A directed edge w:A → w:B exists for each path w:A → tx:T → w:B,
    with attributes: txid, amount_btc (B's output amount), timestamp,
    fee_btc, script_type.

verify_bipartite(G) → tuple[bool, list[str]]
    Structural integrity check on G: confirms no wallet→wallet or
    transaction→transaction edges exist, and every transaction node
    has ≥1 SENT in-edge and ≥1 RECEIVED out-edge.

Both G and P are the canonical inputs to the typology detectors.

---

Graph-type rationale
--------------------
G is a ``networkx.MultiDiGraph`` (not a plain DiGraph) for one reason:
defensive correctness.  If the same IP relays the same transaction twice
(duplicate relay events), a plain DiGraph would silently overwrite the first
BROADCAST edge with the second.  MultiDiGraph preserves both.  The v2
dataset guarantees unique (relay_ip, txid) pairs, so in practice there will
be no parallel edges in production — but the type is the right model for the
domain.

Impact on detector code
-----------------------
In a MultiDiGraph, ``G[u][v]`` returns ``{key: edge_data_dict}`` instead of
``edge_data_dict`` directly.  The only place in the detector suite that reads
edge attributes of G directly is ``detectors/mixing.py`` line 96
(``G[tx_id][nbr]["amount_btc"]``).  That one line has been updated as a
mechanical, non-logic change forced by the type upgrade.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

import networkx as nx
import pandas as pd

from graph_engine import config

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API — DataFrame path  (signature unchanged; return type upgraded)
# ---------------------------------------------------------------------------

def build_full_graph(df: pd.DataFrame) -> nx.MultiDiGraph:
    """
    Build the heterogeneous directed graph from the merged DataFrame.

    This is the existing pipeline path.  It now wraps ``iter_records`` →
    ``build_full_graph_from_records`` internally so both paths share a single
    construction kernel.

    Node attribute ``node_type`` discriminates wallet / transaction / ip nodes.
    Edge attribute ``edge_type`` discriminates SENT / RECEIVED / BROADCAST edges.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ``ingest.load_merged_df()``.

    Returns
    -------
    nx.MultiDiGraph
    """
    from graph_engine.ingest import iter_records  # local import avoids circular dep

    log.info("Building full heterogeneous graph from %d transactions …", len(df))
    return build_full_graph_from_records(iter_records(df))


# ---------------------------------------------------------------------------
# Public API — RawTxRecord path  (schema-decoupled)
# ---------------------------------------------------------------------------

def build_full_graph_from_records(
    records: Iterable,
) -> nx.MultiDiGraph:
    """
    Build the heterogeneous directed graph from an iterable of ``RawTxRecord``
    objects (produced by ``ingest.iter_records``).

    This is the schema-decoupled construction kernel.  ``build_full_graph(df)``
    delegates here after converting rows to records.

    Node attribute ``node_type`` discriminates wallet / transaction / ip nodes.
    Edge attribute ``edge_type`` discriminates SENT / RECEIVED / BROADCAST edges.

    Parameters
    ----------
    records : Iterable[RawTxRecord]
        Iterable of valid RawTxRecord objects.

    Returns
    -------
    nx.MultiDiGraph
        Heterogeneous directed multigraph.
    """
    G: nx.MultiDiGraph = nx.MultiDiGraph()
    n_records = 0

    for rec in records:
        n_records += 1
        tx_id = f"{config.PREFIX_TX}{rec.txid}"
        ip_id = f"{config.PREFIX_IP}{rec.network.relay_ip}"

        # ------------------------------------------------------------------ #
        # Transaction node                                                     #
        # ------------------------------------------------------------------ #
        ts = rec.timestamp
        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)

        G.add_node(
            tx_id,
            node_type        = "transaction",
            txid             = rec.txid,
            timestamp        = ts,
            timestamp_iso    = ts_iso,
            fee_btc          = rec.fee_btc,
            script_type      = rec.script_type,
            scenario_id      = rec.scenario_id or "",
            split            = rec.split or "",
            num_inputs       = len(rec.inputs),
            num_outputs      = len(rec.outputs),
            total_input_btc  = rec.total_input_btc,
            total_output_btc = rec.total_output_btc,
        )

        # ------------------------------------------------------------------ #
        # IP node  (idempotent — first occurrence wins for static attributes) #
        # ------------------------------------------------------------------ #
        net = rec.network
        relay_ts     = net.relay_timestamp
        relay_ts_iso = relay_ts.isoformat() if hasattr(relay_ts, "isoformat") else str(relay_ts)

        if ip_id not in G:
            G.add_node(
                ip_id,
                node_type       = "ip",
                relay_ip        = net.relay_ip,
                country_code    = net.country_code,
                asn             = net.asn,
                isp             = net.isp,
                node_type_infra = net.node_type,   # renamed to avoid collision with node_type
                relay_port      = net.relay_port,
            )

        # BROADCAST edge: IP → Transaction
        G.add_edge(
            ip_id, tx_id,
            edge_type           = "BROADCAST",
            relay_timestamp     = relay_ts,
            relay_timestamp_iso = relay_ts_iso,
            relay_port          = net.relay_port,
            user_agent          = net.user_agent,
        )

        # ------------------------------------------------------------------ #
        # Wallet nodes + SENT edges  (input side)                             #
        # ------------------------------------------------------------------ #
        for entry in rec.inputs:
            w_id = f"{config.PREFIX_WALLET}{entry.address}"
            if w_id not in G:
                G.add_node(w_id, node_type="wallet", address=entry.address)
            # SENT: Wallet → Transaction
            G.add_edge(
                w_id, tx_id,
                edge_type  = "SENT",
                amount_btc = entry.amount_btc,
            )

        # ------------------------------------------------------------------ #
        # Wallet nodes + RECEIVED edges  (output side)                        #
        # ------------------------------------------------------------------ #
        for entry in rec.outputs:
            w_id = f"{config.PREFIX_WALLET}{entry.address}"
            if w_id not in G:
                G.add_node(w_id, node_type="wallet", address=entry.address)
            # RECEIVED: Transaction → Wallet
            G.add_edge(
                tx_id, w_id,
                edge_type  = "RECEIVED",
                amount_btc = entry.amount_btc,
            )

    log.info("Graph construction complete: %d records processed", n_records)
    _log_graph_stats(G)
    return G


# ---------------------------------------------------------------------------
# Public API — Wallet projection
# ---------------------------------------------------------------------------

def build_wallet_projection(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Build the wallet-to-wallet transfer graph from the full heterogeneous graph.

    For each path  w:A -[SENT]→ tx:T -[RECEIVED]→ w:B  in G, add a directed
    edge  w:A → w:B  in the projection carrying full per-transaction metadata:
        txid        : int
        amount_btc  : float  (the RECEIVED amount for B in that tx)
        timestamp   : datetime  (block timestamp of tx:T)
        fee_btc     : float  (miner fee of tx:T)
        script_type : str    (script type of tx:T)

    Multiple transfers between the same wallet pair (from different txs) produce
    separate parallel edges — this is a MultiDiGraph so amounts and metadata
    are never collapsed or aggregated.

    Self-loops (input wallet == output wallet, i.e. UTXO change-address reuse)
    are skipped to avoid polluting traversals.

    Parameters
    ----------
    G : nx.MultiDiGraph
        Output of ``build_full_graph`` or ``build_full_graph_from_records``.

    Returns
    -------
    nx.MultiDiGraph
        Wallet-to-wallet transfer graph preserving per-transaction granularity.
    """
    log.info("Building wallet-to-wallet projection …")
    P: nx.MultiDiGraph = nx.MultiDiGraph()

    for tx_id, tx_data in G.nodes(data=True):
        if tx_data.get("node_type") != "transaction":
            continue

        # --- Wallets that sent to this transaction ---
        # In a MultiDiGraph, G.predecessors(tx_id) yields each predecessor node
        # once.  G[nbr][tx_id] → {edge_key: edge_attr_dict}.
        # We take the first (and typically only) SENT edge per wallet.
        senders: list[tuple[str, float]] = []
        for nbr in G.predecessors(tx_id):
            if G.nodes[nbr].get("node_type") != "wallet":
                continue
            edge_keys = G[nbr][tx_id]               # {key: data_dict}
            for _k, edge_data in edge_keys.items():
                if edge_data.get("edge_type") == "SENT":
                    senders.append((nbr, edge_data["amount_btc"]))
                    break  # one SENT edge per (wallet, tx) pair suffices

        # --- Wallets that received from this transaction ---
        receivers: list[tuple[str, float]] = []
        for nbr in G.successors(tx_id):
            if G.nodes[nbr].get("node_type") != "wallet":
                continue
            edge_keys = G[tx_id][nbr]               # {key: data_dict}
            for _k, edge_data in edge_keys.items():
                if edge_data.get("edge_type") == "RECEIVED":
                    receivers.append((nbr, edge_data["amount_btc"]))
                    break  # one RECEIVED edge per (tx, wallet) pair suffices

        if not senders or not receivers:
            continue

        ts          = tx_data["timestamp"]
        txid        = tx_data["txid"]
        fee_btc     = tx_data["fee_btc"]
        script_type = tx_data["script_type"]

        # Ensure wallet nodes exist in projection (copy node attributes from G)
        for w, _ in senders + receivers:
            if w not in P:
                P.add_node(w, **G.nodes[w])

        # One edge per (sender, receiver) pair per transaction
        for s_addr, _s_amt in senders:
            for r_addr, r_amt in receivers:
                if s_addr == r_addr:
                    # Skip self-loops: change-address returning to same wallet
                    continue
                P.add_edge(
                    s_addr, r_addr,
                    txid        = txid,
                    amount_btc  = r_amt,
                    timestamp   = ts,
                    fee_btc     = fee_btc,
                    script_type = script_type,
                )

    log.info(
        "Wallet projection: %d wallet nodes, %d transfer edges",
        P.number_of_nodes(),
        P.number_of_edges(),
    )
    return P


# ---------------------------------------------------------------------------
# Public API — Bipartite verification
# ---------------------------------------------------------------------------

def verify_bipartite(G: nx.MultiDiGraph) -> tuple[bool, list[str]]:
    """
    Verify that G maintains its intended bipartite-like structure.

    The following structural invariants must all hold:

    1. No direct wallet → wallet edges exist.
    2. No direct transaction → transaction edges exist.
    3. Every transaction node has at least one SENT in-edge (from a wallet).
    4. Every transaction node has at least one RECEIVED out-edge (to a wallet).

    Parameters
    ----------
    G : nx.MultiDiGraph
        The full heterogeneous graph.

    Returns
    -------
    (ok, violations) : tuple[bool, list[str]]
        ``ok`` is True only when the violations list is empty.
    """
    violations: list[str] = []

    for u, v, edge_data in G.edges(data=True):
        u_type = G.nodes[u].get("node_type")
        v_type = G.nodes[v].get("node_type")
        if u_type == "wallet" and v_type == "wallet":
            violations.append(
                f"ILLEGAL wallet→wallet edge: {u} → {v}  "
                f"(edge_type={edge_data.get('edge_type', 'n/a')})"
            )
        if u_type == "transaction" and v_type == "transaction":
            violations.append(
                f"ILLEGAL transaction→transaction edge: {u} → {v}  "
                f"(edge_type={edge_data.get('edge_type', 'n/a')})"
            )

    for tx_id, tx_data in G.nodes(data=True):
        if tx_data.get("node_type") != "transaction":
            continue

        has_sent = any(
            G.nodes[nbr].get("node_type") == "wallet"
            and any(
                ed.get("edge_type") == "SENT"
                for ed in G[nbr][tx_id].values()
            )
            for nbr in G.predecessors(tx_id)
        )
        if not has_sent:
            violations.append(
                f"Transaction {tx_id} has no SENT in-edge from a wallet"
            )

        has_received = any(
            G.nodes[nbr].get("node_type") == "wallet"
            and any(
                ed.get("edge_type") == "RECEIVED"
                for ed in G[tx_id][nbr].values()
            )
            for nbr in G.successors(tx_id)
        )
        if not has_received:
            violations.append(
                f"Transaction {tx_id} has no RECEIVED out-edge to a wallet"
            )

    ok = len(violations) == 0
    if ok:
        log.info("verify_bipartite: PASS — all structural invariants hold")
    else:
        log.error(
            "verify_bipartite: FAIL — %d violation(s): %s",
            len(violations), violations[:5],  # log first 5 to avoid spam
        )
    return ok, violations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _log_graph_stats(G: nx.MultiDiGraph) -> None:
    node_types: dict[str, int] = {}
    edge_types: dict[str, int] = {}

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
