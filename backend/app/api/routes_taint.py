"""
Forward Taint Tracking & Risk Propagation Route.
"""
from fastapi import APIRouter, Query, HTTPException
from backend.app.services.taint_service import taint_service
from backend.app.services.data_service import data_service
from backend.app.models.schemas import TaintResponse

router = APIRouter(tags=["Forensics"])

@router.get("/taint", response_model=TaintResponse)
def track_taint_flow(
    seed_address: str = Query(..., description="Flagged illicit seed Bitcoin address"),
    decay_rate: float = Query(0.85, ge=0.1, le=1.0, description="Per-hop distance decay factor"),
    max_depth: int = Query(5, ge=1, le=8, description="Maximum forward tracing depth"),
    min_taint: float = Query(0.01, ge=0.0001, le=0.5, description="Minimum taint sensitivity threshold")
):
    """
    Computes forward dirty coin propagation (Haircut & FIFO models) from a seed address.
    Returns contaminated destination addresses, taint percentages, hop distances, and contaminated volume.
    """
    if seed_address not in data_service.unique_wallets:
        raise HTTPException(
            status_code=404,
            detail=f"Seed address '{seed_address}' not found in blockchain ledger."
        )
    return taint_service.propagate_taint(
        seed_address=seed_address,
        decay_rate=decay_rate,
        max_depth=max_depth,
        min_taint_threshold=min_taint
    )
