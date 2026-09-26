"""Landing-page model/data analytics; all handlers are read-only."""
from typing import Literal

from fastapi import APIRouter, Query

from backend.app.models.observatory import (
    DatasetData, Diagram, FeatureData, ObservatoryResponse, OverviewData,
    PatternsData, PerformanceData,
)
from backend.app.services.observatory_service import observatory_service

router = APIRouter(prefix="/api/observatory", tags=["Observatory"])


@router.get("/overview", response_model=ObservatoryResponse[OverviewData])
def overview():
    """Headline metadata and binary metrics from the saved V9 frozen evaluation."""
    return observatory_service.overview()


@router.get("/dataset", response_model=ObservatoryResponse[DatasetData])
def dataset(bucket: Literal["day", "week", "month"] = Query("month")):
    """Bundled V9 dataset aggregations. UTC buckets; Monday-start weeks."""
    return observatory_service.dataset(bucket)


@router.get("/performance", response_model=ObservatoryResponse[PerformanceData])
def performance():
    """Frozen binary/typology results, confusion matrices and diagnostics."""
    return observatory_service.performance()


@router.get("/features", response_model=ObservatoryResponse[FeatureData])
def features(
    model: Literal["binary", "typology"] = Query("binary"),
    limit: int = Query(15, ge=1, le=46),
):
    """Normalized split gain read from a local V9 model; performs no inference."""
    return observatory_service.features(model, limit)


@router.get("/pipeline", response_model=ObservatoryResponse[Diagram])
def pipeline():
    """Architecture nodes and edges suitable for a flowchart library."""
    return observatory_service.pipeline()


@router.get("/patterns", response_model=ObservatoryResponse[PatternsData])
def patterns():
    """Explicitly illustrative pattern diagrams, with stable local IDs."""
    return observatory_service.patterns()
