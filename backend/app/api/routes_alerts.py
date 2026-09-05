"""
Alert Triage & Explainable Evidence Routes.
Provides dynamically detected candidate alerts and deep SHAP feature attributions.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.app.models.schemas import (
    AlertListResponse,
    EvidenceResponse
)
from backend.app.services.typology_detector import typology_detector

router = APIRouter(tags=["Alerts"])

@router.get("/alerts", response_model=AlertListResponse)
def get_alerts(
    min_confidence: float = Query(
        0.50,
        ge=0.0,
        le=1.0,
        description="Minimum typology confidence filter",
    ),
    pattern_type: Optional[str] = Query(None, description="Filter by typology: peeling_chain, layering, mixing, ransomware"),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Retrieve dynamically detected and ranked candidate alerts.
    Filters by minimum typology confidence and specific laundering typologies.
    """
    alerts = typology_detector.get_alerts(
        min_confidence=min_confidence,
        pattern_type=pattern_type,
        limit=limit
    )
    return AlertListResponse(
        total_alerts=len(alerts),
        alerts=alerts
    )

@router.get("/alerts/{candidate_id}/evidence", response_model=EvidenceResponse)
def get_alert_evidence(candidate_id: str):
    """
    Retrieve full explainable forensic dossier for a flagged candidate structure,
    including SHAP feature attributions, heuristic metrics, and dual-layer telemetry.
    """
    evidence = typology_detector.get_evidence(candidate_id)
    if not evidence:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate alert '{candidate_id}' not found in registry."
        )
    return evidence
