"""
System Health & Diagnostics Route.
"""
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.data_service import data_service
from backend.app.services.clustering_service import clustering_service
from backend.app.services.typology_detector import typology_detector
from backend.app.models.schemas import HealthResponse

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
def get_health():
    """Returns runtime system status, loaded transaction count, and uptime."""
    stats = data_service.get_stats()
    return HealthResponse(
        status="ONLINE" if data_service.is_ready else "INITIALIZING",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        loaded_transactions=stats["loaded_transactions"],
        unique_scenarios=stats["unique_scenarios"],
        unique_wallets=stats["unique_wallets"],
        uptime_seconds=stats["uptime_seconds"],
        alert_count=len(typology_detector.detected_alerts) if typology_detector.is_scanned else 0,
        cluster_count=len(clustering_service.cluster_members),
        illicit_ratio_note="Scenario-level ML; transaction-level illicit ratio unavailable.",
    )
