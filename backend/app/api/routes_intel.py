"""
Tor & Threat Intelligence Profiler API Routes.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Query, Body, HTTPException
from backend.app.services.tor_profiler import tor_profiler

router = APIRouter(prefix="/api/intel", tags=["Threat Intelligence & Tor Profiler"])

class TorProfileRequest(BaseModel):
    txid: int

@router.get("/tor-summary")
def get_tor_summary():
    """
    Returns aggregated metrics across all Tor and proxy exit nodes in the network.
    """
    return tor_profiler.get_tor_network_summary()

@router.get("/tor-profiler/{txid}")
def profile_tor_by_txid(txid: int):
    """
    Analyzes timing entropy, relay jitter, and CIOH cluster attribution for a suspect transaction.
    """
    res = tor_profiler.profile_tor_transaction(txid)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/tor-profiler")
def profile_tor_post(payload: TorProfileRequest):
    """
    POST variant for inspecting Tor timing entropy and circuit correlation.
    """
    res = tor_profiler.profile_tor_transaction(payload.txid)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res
