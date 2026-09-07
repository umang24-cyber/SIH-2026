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
    if scenario_id in data_service.scenario_tx_map:
        return scenario_id
    if scenario_id in SCENARIO_ALIASES and SCENARIO_ALIASES[scenario_id] in data_service.scenario_tx_map:
        return SCENARIO_ALIASES[scenario_id]
    low = scenario_id.lower()
    prefix_map = {
        "licit": "normal_",
        "ransom": "ransomware_",
        "peel": "peeling_chain_",
        "mix": "mixing_",
        "layer": "normal_",
    }
    for p, target_p in prefix_map.items():
        if low.startswith(p):
            for real_s in data_service.scenario_tx_map:
                if real_s.startswith(target_p):
                    return real_s
    if low in ["default", "root", "sample", "0", "1", ""]:
        return next(iter(data_service.scenario_tx_map.keys()), scenario_id)
    return scenario_id

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
    Partitions nodes into modular syndicates / co-acting clusters using NetworkX greedy modularity.
    """
    resolved_id = _resolve_scenario_id(scenario_id)
    txids = data_service.get_scenario_txids(resolved_id)
    if not txids:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario ID '{scenario_id}' not found in cluster database."
        )
    return community_service.detect_communities(resolved_id)
