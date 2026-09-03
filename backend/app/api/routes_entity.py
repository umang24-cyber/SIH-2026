"""
Entity / Wallet Forensics & CIOH Clustering Routes.
"""
from fastapi import APIRouter, HTTPException
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.models.schemas import EntityResponse, ClusterResponse

router = APIRouter(tags=["Entity"])

@router.get("/entity/{address}", response_model=EntityResponse)
def get_entity_profile(address: str):
    """
    Retrieve wallet activity profile, financial volume, transaction counts,
    and exchange status computed dynamically from the master dataset.
    """
    entity = data_service.get_entity(address)
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Bitcoin address '{address}' not found in forensic ledger."
        )
    return entity

@router.get("/entity/{address}/cluster", response_model=ClusterResponse)
def get_entity_cluster(address: str):
    """
    Common-Input Ownership Heuristic (CIOH) Clustering:
    Returns all co-owned Bitcoin addresses, multi-input transaction counts,
    and total combined financial volume for the entity.
    """
    cluster = clustering_service.get_entity_cluster(address)
    if not cluster:
        raise HTTPException(
            status_code=404,
            detail=f"Bitcoin address '{address}' not found in cluster registry."
        )
    return cluster
