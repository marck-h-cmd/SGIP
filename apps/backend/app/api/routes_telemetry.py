from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.services.telemetry_service import TelemetryService
from app.schemas.telemetry_schema import (
    TelemetryResponse,
    TelemetryHistoryResponse,
    TelemetrySummary,
    TelemetryFilter
)
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])


@router.get("/latest")
async def get_latest_readings(
    dma_id: Optional[str] = Query(None, description="Filter by DMA ID"),
    service: TelemetryService = Depends()
) -> List[TelemetryResponse]:
    """Get latest telemetry readings"""
    readings = service.get_latest_readings(dma_id)
    return [TelemetryResponse(**r.dict()) for r in readings]


@router.get("/history/{dma_id}")
async def get_historical_readings(
    dma_id: str,
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    limit: int = Query(1000, le=10000, description="Limit results"),
    service: TelemetryService = Depends()
) -> TelemetryHistoryResponse:
    """Get historical readings for a DMA"""
    readings = service.get_historical_readings(dma_id, start_date, end_date, limit)
    
    if not readings:
        raise NotFoundException("Readings", f"DMA {dma_id} in period")
    
    return TelemetryHistoryResponse(
        dma_id=dma_id,
        dma_name=readings[0].dma_name,
        readings=[TelemetryResponse(**r.dict()) for r in readings],
        total_count=len(readings),
        start_date=start_date,
        end_date=end_date
    )


@router.get("/summary/{dma_id}")
async def get_dma_summary(
    dma_id: str,
    service: TelemetryService = Depends()
) -> TelemetrySummary:
    """Get summary for a DMA"""
    summary = service.get_dma_summary(dma_id)
    if not summary:
        raise NotFoundException("DMA", dma_id)
    
    current = summary.get("current_reading")
    stats = summary.get("statistics", {})
    
    return TelemetrySummary(
        dma_id=dma_id,
        dma_name=summary.get("dma_name", ""),
        current_pressure=current.pressure_mca if current else None,
        current_flow=current.flow_lps if current else None,
        avg_pressure_24h=stats.get("avg_pressure"),
        avg_flow_24h=stats.get("avg_flow"),
        max_pressure_24h=stats.get("max_pressure"),
        min_pressure_24h=stats.get("min_pressure"),
        max_flow_24h=stats.get("max_flow"),
        min_flow_24h=stats.get("min_flow"),
        sample_count_24h=stats.get("sample_count", 0),
        last_update=datetime.utcnow()
    )


@router.get("/trends/{dma_id}")
async def get_dma_trends(
    dma_id: str,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    service: TelemetryService = Depends()
):
    """Get pressure and flow trends for a DMA"""
    trends = service.get_dma_trends(dma_id, hours)
    if not trends.get("pressure"):
        raise NotFoundException("Trends", f"DMA {dma_id}")
    return trends


@router.get("/moche/trends")
async def get_moche_trends(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    service: TelemetryService = Depends()
):
    """Get trends specifically for Moche sector"""
    trends = service.get_moche_trends(hours)
    if not trends.get("pressure"):
        raise NotFoundException("Trends", "Moche")
    return trends


@router.get("/moche/latest")
async def get_moche_latest(
    service: TelemetryService = Depends()
) -> TelemetryResponse:
    """Get latest reading for Moche sector"""
    readings = service.get_latest_readings()
    if not readings:
        raise NotFoundException("Readings", "Moche")
    return TelemetryResponse(**readings[0].dict())


@router.get("/dmas")
async def get_all_dmas(
    service: TelemetryService = Depends()
) -> List[dict]:
    """Get all DMAs"""
    return service.get_all_dmas()