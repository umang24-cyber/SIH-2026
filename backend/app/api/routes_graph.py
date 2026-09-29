"""
Graph Link-Analysis & Community Partitioning Routes.
"""
from fastapi import APIRouter, HTTPException
from backend.app.services.data_service import data_service
from backend.app.services.graph_service import graph_service
from backend.app.services.community_service import community_service
from backend.app.models.schemas import GraphResponse

router = APIRouter(tags=["Graph"])

SCENARIO_ALIASES = {
    "licit_00001": "normal_00002",
    "ransom_0001": "ransomware_03287",
    "peeling_0001": "peeling_chain_04651",
    "mixing_0001": "mixing_05246",
    "layering_0001": "normal_02462",
}

def _resolve_scenario_id(scenario_id: str) -> str:
    target = str(scenario_id).strip()
    if target in data_service.scenario_tx_map:
        return target
    if target in SCENARIO_ALIASES and SCENARIO_ALIASES[target] in data_service.scenario_tx_map:
        return SCENARIO_ALIASES[target]

    # 1. Direct numeric or string TXID lookup
    try:
        tx_num = int(target)
        if tx_num in data_service.txid_map:
            sc = data_service.txid_map[tx_num].get("scenario_id")
            if sc and sc in data_service.scenario_tx_map:
                return sc
    except (ValueError, TypeError):
        pass

    for tx in data_service.txid_map.values():
        if str(tx.get("transaction_hash", "")) == target or str(tx.get("txid", "")) == target:
            sc = tx.get("scenario_id")
            if sc and sc in data_service.scenario_tx_map:
                return sc
            break

    # 2. Bitcoin address lookup (map address to its scenario)
    addrs_txs = data_service.address_in_map.get(target) or data_service.address_out_map.get(target)
    if addrs_txs:
        for tid in addrs_txs:
            sc = data_service.txid_map.get(tid, {}).get("scenario_id")
            if sc and sc in data_service.scenario_tx_map:
                return sc

    low = target.lower()
    clean = low.replace("sample_", "").replace("live_", "").replace("test_", "")

    # 3. Fuzzy substring match against indexed scenario keys
    for real_s in data_service.scenario_tx_map:
        real_low = real_s.lower()
        if low in real_low or clean in real_low or real_low in low:
            return real_s

    # 4. Fallback prefix resolution
    prefix_map = {
        "licit": "normal_",
        "ransom": "ransomware_",
        "peel": "peeling_chain_",
        "mix": "mixing_",
        "layer": "normal_",
    }
    for p, target_p in prefix_map.items():
        if low.startswith(p) or clean.startswith(p):
            for real_s in data_service.scenario_tx_map:
                if real_s.startswith(target_p):
                    return real_s

    if low in ["default", "root", "sample", "0", "1", ""]:
        return next(iter(data_service.scenario_tx_map.keys()), target)
    return target

import time
from collections import defaultdict

_graph_rate_limit: dict[str, list[float]] = defaultdict(list)
_MAX_GRAPH_REQUESTS_PER_WINDOW = 12
_RATE_WINDOW_SECONDS = 3.0

def _check_graph_rate_limit(client_id: str = "global"):
    now = time.time()
    valid_times = [t for t in _graph_rate_limit[client_id] if now - t < _RATE_WINDOW_SECONDS]
    if len(valid_times) >= _MAX_GRAPH_REQUESTS_PER_WINDOW:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded for graph requests (max 12 requests per 3s). Please slow down."
        )
    valid_times.append(now)
    _graph_rate_limit[client_id] = valid_times

@router.get("/graph/{scenario_id}", response_model=GraphResponse)
def get_scenario_graph(scenario_id: str):
    """
    Retrieve heterogeneous graph representation for a scenario:
    - Nodes: Wallet, Transaction, and IP nodes
    - Edges: SENT, RECEIVED, and BROADCAST edges
    """
    _check_graph_rate_limit()
    resolved_id = _resolve_scenario_id(scenario_id)
    txids = data_service.get_scenario_txids(resolved_id)
    if not txids:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario ID '{scenario_id}' not found in cluster database."
        )
    return graph_service.build_scenario_graph(resolved_id)

@router.get("/graph/{scenario_id}/communities")
def get_scenario_communities(scenario_id: str):
    """
    Community Detection on Transaction Graph:
    Partitions nodes into modular entity clusters / co-acting clusters using NetworkX greedy modularity.
    """
    resolved_id = _resolve_scenario_id(scenario_id)
    txids = data_service.get_scenario_txids(resolved_id)
    if not txids:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario ID '{scenario_id}' not found in cluster database."
        )
    return community_service.detect_communities(resolved_id)
