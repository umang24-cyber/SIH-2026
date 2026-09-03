"""
detectors/peeling_chain.py — Peeling-chain typology detector.

Algorithm summary
-----------------
1. Operate on the wallet-to-wallet MultiDiGraph projection (P).
2. A *peel transaction* satisfies:
     - exactly 1 or 2 unique input wallets (the UTXO sender(s))
     - exactly 2 unique output wallets
     - The carry-forward output (larger amount) is the wallet address that
       will appear as input in the NEXT transaction in the chain.
3. Seed discovery: for each transaction node in the full graph G, check if it
   is a peel transaction (1–2 inputs, 2 outputs, amounts with clear split).
4. Chain extension: from the carry-forward wallet, greedily extend the chain
   following the next peel transaction, checking:
     a. Time gap between consecutive transactions ≤ PEEL_MAX_HOP_GAP_SECONDS
     b. Carry-forward amount strictly decreases at each hop
     c. Next transaction is also a peel transaction (2 outputs)
5. Accept chains of length ≥ PEEL_MIN_CHAIN_LENGTH.
6. Deduplication: if chain A's txids are a strict subset of chain B's, drop A.
"""

from __future__ import annotations

import itertools
import logging
from datetime import timedelta, timezone

import networkx as nx

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
    Detect peeling-chain candidate structures.

    Parameters
    ----------
    G : nx.DiGraph
        Full heterogeneous graph (wallet / transaction / ip nodes).
    P : nx.MultiDiGraph
        Wallet-to-wallet projection.

    Returns
    -------
    list[CandidateStructure]
        One entry per detected peeling chain.
    """
    log.info("Peeling-chain detector: scanning %d transaction nodes …", _tx_count(G))

    # Build an index: txid (int) → tx node data, for fast lookup
    tx_index: dict[int, dict] = {
        data["txid"]: (node_id, data)
        for node_id, data in G.nodes(data=True)
        if data.get("node_type") == "transaction"
    }

    # Build an index: wallet_address → list of (txid, amount_btc, timestamp)
    # for SENT edges (input side) — needed to find "what tx used this wallet next"
    wallet_to_sent_txs: dict[str, list[tuple[int, float]]] = {}
    for src, dst, edata in G.edges(data=True):
        if edata.get("edge_type") == "SENT":
            # src = "w:<addr>", dst = "tx:<txid>"
            addr = G.nodes[src].get("address", "")
            txid_int = G.nodes[dst].get("txid")
            amt = edata.get("amount_btc", 0.0)
            if addr and txid_int is not None:
                wallet_to_sent_txs.setdefault(addr, []).append((txid_int, amt))

    # Build an index: txid → [(output_wallet_addr, amount_btc)]
    tx_to_outputs: dict[int, list[tuple[str, float]]] = {}
    for src, dst, edata in G.edges(data=True):
        if edata.get("edge_type") == "RECEIVED":
            txid_int = G.nodes[src].get("txid")
            addr     = G.nodes[dst].get("address", "")
            amt      = edata.get("amount_btc", 0.0)
            if txid_int is not None and addr:
                tx_to_outputs.setdefault(txid_int, []).append((addr, amt))

    # Build an index: txid → [(input_wallet_addr, amount_btc)]
    tx_to_inputs: dict[int, list[tuple[str, float]]] = {}
    for src, dst, edata in G.edges(data=True):
        if edata.get("edge_type") == "SENT":
            addr     = G.nodes[src].get("address", "")
            txid_int = G.nodes[dst].get("txid")
            amt      = edata.get("amount_btc", 0.0)
            if txid_int is not None and addr:
                tx_to_inputs.setdefault(txid_int, []).append((addr, amt))

    chains: list[list[_Hop]] = []

    # Identify seed transactions (potential first hop of a peel chain)
    candidate_seeds = [
        txid for txid, (_, data) in tx_index.items()
        if _is_peel_tx(txid, tx_to_inputs, tx_to_outputs)
    ]
    log.info("  %d peel-transaction seeds found", len(candidate_seeds))

    for seed_txid in candidate_seeds:
        chain = _extend_chain(
            seed_txid, tx_index, tx_to_inputs, tx_to_outputs, wallet_to_sent_txs
        )
        if chain and len(chain) >= config.PEEL_MIN_CHAIN_LENGTH:
            chains.append(chain)

    # Deduplicate: drop chains whose txid set is a strict subset of another
    chains = _deduplicate(chains)

    log.info("Peeling-chain detector: %d candidate chains after dedup", len(chains))

    # Convert to CandidateStructure objects
    candidates: list[CandidateStructure] = []
    for i, chain in enumerate(chains):
        cid = f"peel_{i+1:04d}"
        member_txids   = [h.txid for h in chain]
        member_wallets = list(dict.fromkeys(
            [h.from_wallet for h in chain] + [chain[-1].to_wallet]
        ))

        amounts    = [h.carry_amount for h in chain]
        timestamps = [h.timestamp for h in chain]
        time_gaps  = [
            (timestamps[j+1] - timestamps[j]).total_seconds()
            for j in range(len(timestamps) - 1)
        ] if len(timestamps) > 1 else [0.0]

        decay_rate = amounts[-1] / amounts[0] if amounts[0] > 0 else 0.0
        total_peeled = sum(h.peeled_amount for h in chain if h.peeled_amount is not None)

        hop_seq = [
            {
                "hop":          idx + 1,
                "from_wallet":  h.from_wallet,
                "to_wallet":    h.to_wallet,
                "txid":         h.txid,
                "amount_btc":   h.carry_amount,
                "peeled_btc":   h.peeled_amount,
                "timestamp":    h.timestamp.isoformat() if h.timestamp else None,
            }
            for idx, h in enumerate(chain)
        ]

        candidates.append(CandidateStructure(
            candidate_id   = cid,
            candidate_type = "peeling_chain",
            member_txids   = member_txids,
            member_wallets = member_wallets,
            features       = {
                "chain_length":         len(chain),
                "total_peeled_btc":     round(total_peeled, 8),
                "amount_decay_rate":    round(decay_rate, 6),
                "avg_time_gap_seconds": round(sum(time_gaps) / len(time_gaps), 1),
                "min_time_gap_seconds": round(min(time_gaps), 1),
                "max_time_gap_seconds": round(max(time_gaps), 1),
                "total_btc_moved":      round(amounts[0], 8),
                "time_span_seconds":    round(sum(time_gaps), 1),
                # network features filled in by features.py
                "unique_ips":           None,
                "unique_asns":          None,
                "tor_vpn_fraction":     None,
            },
            hop_sequence = hop_seq,
        ))

    return candidates


# ---------------------------------------------------------------------------
# Internal data types
# ---------------------------------------------------------------------------

class _Hop:
    """One hop in a peeling chain."""
    __slots__ = ("txid", "from_wallet", "to_wallet", "carry_amount",
                 "peeled_amount", "timestamp")

    def __init__(self, txid, from_wallet, to_wallet, carry_amount,
                 peeled_amount, timestamp):
        self.txid          = txid
        self.from_wallet   = from_wallet
        self.to_wallet     = to_wallet        # carry-forward wallet
        self.carry_amount  = carry_amount     # amount going forward
        self.peeled_amount = peeled_amount    # amount peeled off (payment)
        self.timestamp     = timestamp


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tx_count(G: nx.DiGraph) -> int:
    return sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "transaction")


def _is_peel_tx(
    txid: int,
    tx_to_inputs:  dict[int, list[tuple[str, float]]],
    tx_to_outputs: dict[int, list[tuple[str, float]]],
) -> bool:
    """
    Return True if the transaction matches the peel pattern:
      - 1–2 distinct input wallets
      - exactly 2 distinct output wallets
    """
    inputs  = tx_to_inputs.get(txid, [])
    outputs = tx_to_outputs.get(txid, [])

    if not (1 <= len(set(a for a, _ in inputs)) <= 2):
        return False
    if len(set(a for a, _ in outputs)) != 2:
        return False
    return True


def _extend_chain(
    seed_txid:       int,
    tx_index:        dict[int, tuple[str, dict]],
    tx_to_inputs:    dict[int, list[tuple[str, float]]],
    tx_to_outputs:   dict[int, list[tuple[str, float]]],
    wallet_to_sent:  dict[str, list[tuple[int, float]]],
) -> list[_Hop] | None:
    """
    Greedily extend a peeling chain starting from seed_txid.
    Returns the list of hops, or None if the chain is shorter than the minimum.
    """
    chain: list[_Hop] = []
    visited_txids: set[int] = set()

    current_txid = seed_txid

    while True:
        if current_txid in visited_txids:
            break
        visited_txids.add(current_txid)

        if current_txid not in tx_index:
            break

        _node_id, tx_data = tx_index[current_txid]
        ts = tx_data.get("timestamp")

        outputs = tx_to_outputs.get(current_txid, [])
        if len(outputs) != 2:
            break

        # Sort outputs: larger amount = carry-forward, smaller = peeled payment
        outputs_sorted = sorted(outputs, key=lambda x: x[1], reverse=True)
        carry_wallet, carry_amt = outputs_sorted[0]
        peeled_wallet, peeled_amt = outputs_sorted[1]

        # Determine the "from wallet" (primary input)
        inputs = tx_to_inputs.get(current_txid, [])
        from_wallet = inputs[0][0] if inputs else ""

        hop = _Hop(
            txid          = current_txid,
            from_wallet   = from_wallet,
            to_wallet     = carry_wallet,
            carry_amount  = carry_amt,
            peeled_amount = peeled_amt,
            timestamp     = ts,
        )
        chain.append(hop)

        # --- Try to follow carry_wallet into the next transaction ---
        next_txs = wallet_to_sent.get(carry_wallet, [])
        # Filter: only peel transactions not yet visited
        next_peel = [
            (ntxid, namt) for ntxid, namt in next_txs
            if ntxid not in visited_txids
            and _is_peel_tx(ntxid, tx_to_inputs, tx_to_outputs)
        ]

        if not next_peel:
            break

        # Pick the next tx that:
        # 1. Happens after the current tx
        # 2. Within the max hop gap
        # 3. Has a lower carry-forward amount (amount decreases)
        best_next = None
        for ntxid, namt in next_peel:
            if ntxid not in tx_index:
                continue
            _, ndata = tx_index[ntxid]
            nts = ndata.get("timestamp")
            if nts is None or ts is None:
                continue
            gap = (nts - ts).total_seconds()
            if gap < 0 or gap > config.PEEL_MAX_HOP_GAP_SECONDS:
                continue
            # Amount should decrease (carry-forward of next tx)
            n_outputs = tx_to_outputs.get(ntxid, [])
            if len(n_outputs) != 2:
                continue
            n_carry_amt = max(a for _, a in n_outputs)
            # Allow slight tolerance for fee fluctuations
            tol = config.PEEL_AMOUNT_TOLERANCE * carry_amt
            if n_carry_amt > carry_amt + tol:
                continue
            best_next = (ntxid, nts)
            break

        if best_next is None:
            break

        current_txid = best_next[0]

    return chain if len(chain) >= config.PEEL_MIN_CHAIN_LENGTH else None


def _deduplicate(chains: list[list[_Hop]]) -> list[list[_Hop]]:
    """Remove chains whose txid set is a strict subset of another chain."""
    sets = [frozenset(h.txid for h in c) for c in chains]
    keep = []
    for i, c in enumerate(chains):
        dominated = any(
            sets[i] < sets[j]  # strict subset
            for j in range(len(chains)) if j != i
        )
        if not dominated:
            keep.append(c)
    return keep
