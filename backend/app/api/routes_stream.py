"""
Stream Ingestion & Temporal Sliding-Window Correlation API Routes.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Query, Body, HTTPException
from fastapi.responses import StreamingResponse
from backend.app.services.streaming_correlator import streaming_correlator

router = APIRouter(prefix="/api/stream", tags=["Stream Correlation"])

class ReconcileRequest(BaseModel):
    mempool_stream: List[Dict[str, Any]]
    block_stream: List[Dict[str, Any]]
    max_window_seconds: float = 120.0

@router.get("/replay")
async def stream_replay(
    speed: float = Query(15.0, description="Transactions per second (1 - 100)", ge=1.0, le=100.0),
    limit: int = Query(100, description="Max events to stream", ge=1, le=1000),
    scenario_id: Optional[str] = Query(None, description="Optional scenario ID filter")
):
    """
    Live Server-Sent Events (SSE) transaction stream with real-time heuristic scoring and alert flags.
    Connect frontend EventSource / fetch stream to this endpoint.
    """
    return StreamingResponse(
        streaming_correlator.generate_replay_stream(
            speed_tx_per_sec=speed,
            max_events=limit,
            scenario_id=scenario_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/batch")
def get_stream_batch(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tor_only: bool = Query(False, description="Filter Tor exit node transactions only")
):
    """
    Snapshot of live telemetry stream for dashboard polling.
    """
    return streaming_correlator.get_live_batch(limit=limit, offset=offset, filter_tor=tor_only)

@router.post("/reconcile")
def reconcile_streams(payload: ReconcileRequest):
    """
    Temporal Sliding-Window Correlation Engine:
    Reconciles asynchronous, out-of-order mempool gossip frames with block events.
    """
    return streaming_correlator.reconcile_asynchronous_streams(
        mempool_stream=payload.mempool_stream,
        block_stream=payload.block_stream,
        max_window_seconds=payload.max_window_seconds
    )
