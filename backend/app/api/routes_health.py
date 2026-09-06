"""
System Health & Diagnostics Route.
"""
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.data_service import data_service
from backend.app.models.schemas import HealthResponse

router = APIRouter(tags=["System"])

@router.get("/health", response_model=HealthResponse)
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
        uptime_seconds=stats["uptime_seconds"]
    )
