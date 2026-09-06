"""
Multi-Hop Path Tracing Route.
"""
from fastapi import APIRouter, Query
from backend.app.services.graph_service import graph_service
from backend.app.models.schemas import TraceResponse

router = APIRouter(tags=["Forensics"])

@router.get("/trace", response_model=TraceResponse)
def trace_fund_flow(
    src: str = Query(..., description="Source Bitcoin wallet address"),
    dst: str = Query(..., description="Destination Bitcoin wallet address"),
    max_depth: int = Query(6, ge=1, le=10, description="Maximum hop search depth")
):
    """
    Computes directed multi-hop transaction path between source and destination wallets.
    Returns hop indices, intermediate txids, transferred BTC amounts, and timestamps.
    """
    return graph_service.find_trace_path(src=src, dst=dst, max_depth=max_depth)
