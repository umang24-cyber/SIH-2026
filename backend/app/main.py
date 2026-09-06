"""
FastAPI Main Application Entry Point for SIH PS146 Bitcoin Forensic Platform.
100% Offline / Air-Gapped Linux & WSL2 compliant.
"""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.services.data_service import data_service
from backend.app.services.typology_detector import typology_detector
from backend.app.services.clustering_service import clustering_service
from backend.app.services.ml_service import ml_service
from backend.app.services.anomaly_service import anomaly_service
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_entity import router as entity_router
from backend.app.api.routes_transaction import router as transaction_router
from backend.app.api.routes_graph import router as graph_router
from backend.app.api.routes_trace import router as trace_router
from backend.app.api.routes_taint import router as taint_router
from backend.app.api.routes_alerts import router as alerts_router
from backend.app.api.routes_search import router as search_router
from backend.app.api.routes_stats import router as stats_router
from backend.app.api.routes_stream import router as stream_router
from backend.app.api.routes_intel import router as intel_router
from backend.app.api.routes_dossier import router as dossier_router
from backend.app.api.routes_anomaly import router as anomaly_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan startup: Ingest master CSVs, cluster multi-input entities, scan typologies, load ML models."""
    logger.info("Starting up BitKaun AML Forensics API (100% Offline Engine)...")
    data_service.initialize()
    ml_service.load_model()
    anomaly_service.load_model()
    clustering_service.build_clusters()
    if not typology_detector.is_scanned:
        typology_detector.scan_all_typologies()
    yield
    logger.info("Shutting down BitKaun AML Forensics API...")

# Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dual-Layer Bitcoin Network Telemetry & On-Chain Forensic Intelligence API (100% Air-Gapped)",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Execution Time Measurement Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
    return response

# Register All API Routers
app.include_router(health_router)
app.include_router(entity_router)
app.include_router(transaction_router)
app.include_router(graph_router)
app.include_router(trace_router)
app.include_router(taint_router)
app.include_router(alerts_router)
app.include_router(search_router)
app.include_router(stats_router)
app.include_router(stream_router)
app.include_router(intel_router)
app.include_router(dossier_router)
app.include_router(anomaly_router)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
