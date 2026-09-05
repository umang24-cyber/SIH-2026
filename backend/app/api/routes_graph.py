"""
Graph Link-Analysis & Community Partitioning Routes.
"""
from fastapi import APIRouter, HTTPException
from backend.app.services.data_service import data_service
from backend.app.services.graph_service import graph_service
from backend.app.services.community_service import community_service
from backend.app.models.schemas import GraphResponse

router = APIRouter(tags=["Graph"])

@router.get("/graph/{scenario_id}", response_model=GraphResponse)
def get_scenario_graph(scenario_id: str):
    """
    Retrieve heterogeneous graph representation for a scenario:
    - Nodes: Wallet, Transaction, and IP nodes
    - Edges: SENT, RECEIVED, and BROADCAST edges
    """
    txids = data_service.get_scenario_txids(scenario_id)
    if not txids:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario ID '{scenario_id}' not found in cluster database."
        )
    return graph_service.build_scenario_graph(scenario_id)

@router.get("/graph/{scenario_id}/communities")
def get_scenario_communities(scenario_id: str):
    """
    Community Detection on Transaction Graph:
    Partitions nodes into modular syndicates / co-acting clusters using NetworkX greedy modularity.
    """
    txids = data_service.get_scenario_txids(scenario_id)
    if not txids:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario ID '{scenario_id}' not found in cluster database."
        )
    return community_service.detect_communities(scenario_id)
