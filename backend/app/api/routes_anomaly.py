"""
Anomaly Detection Routes — Isolation Forest Anomaly/Unusualness Scoring.

Provides per-scenario Anomaly Score (0–100) from the fitted IsolationForest
model.  Completely independent of the XGBoost binary/typology classifiers.
The score measures how unlike normal (licit) Bitcoin behavior a scenario is,
NOT a probability of being illicit.
"""
from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import AnomalyScoreResponse
from backend.app.services.anomaly_service import anomaly_service

router = APIRouter(tags=["Anomaly Detection"])


@router.get("/anomaly/{scenario_id}", response_model=AnomalyScoreResponse)
def get_anomaly_score(scenario_id: str):
    """
    Compute the Isolation Forest Anomaly/Unusualness Score for a scenario.

    Returns a 0–100 score where:
    - 0   = indistinguishable from normal (licit) Bitcoin activity
    - 100 = maximally anomalous relative to the licit reference distribution
    - HIGH label: score >= 70
    - MEDIUM label: score 40–69
    - LOW label: score < 40

    **IMPORTANT**: This score is NOT a probability and is NOT combined with
    the ML risk_score or typology_confidence anywhere in the system.
    It is an independent "Anomaly Analysis" capability as named in SIH PS146.
    """
    result = anomaly_service.score_scenario_id(scenario_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_id}' not found or has no transactions.",
        )
    return AnomalyScoreResponse(**result)
