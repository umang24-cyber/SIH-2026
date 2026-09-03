"""
FastAPI Main Application Entry Point for SIH PS146 Bitcoin Forensic Platform.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.services.data_service import data_service
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_entity import router as entity_router
from backend.app.api.routes_transaction import router as transaction_router
from backend.app.api.routes_graph import router as graph_router
from backend.app.api.routes_trace import router as trace_router
from backend.app.api.routes_alerts import router as alerts_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: Load in-memory master dataset at startup."""
    logger.info("Starting up BitKaun AML Forensics API...")
    data_service.initialize()
    yield
    logger.info("Shutting down BitKaun AML Forensics API...")

# Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Dual-Layer Bitcoin Network Telemetry & On-Chain Forensic Intelligence API",
    lifespan=lifespan
)

# Enable CORS for Frontend Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Routers
app.include_router(health_router)
app.include_router(entity_router)
app.include_router(transaction_router)
app.include_router(graph_router)
app.include_router(trace_router)
app.include_router(alerts_router)

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
