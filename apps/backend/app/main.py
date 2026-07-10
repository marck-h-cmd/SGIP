from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from app.api import (
    telemetry_router,
    anomalies_router,
    incidents_router,
    kpis_router,
    dmas_router
)
from app.api.routes_alerts import router as alerts_router
from app.api.routes_reports import router as reports_router
from app.core.config import settings
from app.core.exceptions import SGIPCAPException
from app.infrastructure.database import db
from app.websocket.websocket_handler import WebSocketHandler
from datetime import datetime
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and services on startup, and clean up on shutdown"""
    # Startup
    db.create_tables()
    print("🚀 SGIP-CAP API - Sector Moche")
    print(f"📍 DMA objetivo: {settings.target_dma}")
    print(f"📊 Data Provider: {settings.data_provider}")
    print(f"🎯 Anomaly Threshold: {settings.anomaly_threshold}")
    print("✅ API iniciada correctamente")
    
    yield
    
    # Shutdown
    print("SGIP-CAP API shutting down...")

# Create FastAPI app
app = FastAPI(
    title="SGIP-CAP API - Sector Moche",
    description="Sistema de Gestión Integral de Pérdidas - Sector Moche",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(telemetry_router)
app.include_router(anomalies_router)
app.include_router(incidents_router)
app.include_router(kpis_router)
app.include_router(dmas_router)
app.include_router(alerts_router)
app.include_router(reports_router)

# WebSocket handler
ws_handler = WebSocketHandler()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await ws_handler.handle_connection(websocket, client_id)


# Exception handlers
@app.exception_handler(SGIPCAPException)
async def sgipcap_exception_handler(request, exc: SGIPCAPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": getattr(exc, "error_code", None),
            "data": getattr(exc, "data", None)
        }
    )


# Included routers later...


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SGIP-CAP API",
        "version": "1.0.0",
        "status": "operational",
        "sector": settings.target_dma_name,
        "data_provider": settings.data_provider
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "sector": settings.target_dma_name
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )