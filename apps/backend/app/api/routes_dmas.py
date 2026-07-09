from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.telemetry_service import TelemetryService
from app.services.kpi_service import KPIService
from app.core.exceptions import NotFoundException
from app.core.config import settings

router = APIRouter(prefix="/api/dmas", tags=["DMAs"])


@router.get("/")
async def get_all_dmas(
    service: TelemetryService = Depends()
) -> List[dict]:
    """Get all DMAs"""
    return service.get_all_dmas()


@router.get("/moche")
async def get_moche_dma(
    service: TelemetryService = Depends()
) -> dict:
    """Get Moche DMA information"""
    dma = service.get_dma_info(settings.target_dma)
    if not dma:
        raise NotFoundException("DMA", settings.target_dma)
    
    summary = service.get_dma_summary(settings.target_dma)
    return {
        "dma": dma,
        "summary": summary
    }


@router.get("/{dma_id}")
async def get_dma_detail(
    dma_id: str,
    service: TelemetryService = Depends()
):
    """Get detailed information about a DMA"""
    dma = service.get_dma_info(dma_id)
    if not dma:
        raise NotFoundException("DMA", dma_id)
    
    summary = service.get_dma_summary(dma_id)
    return {
        "dma": dma,
        "summary": summary
    }


@router.get("/{dma_id}/summary")
async def get_dma_summary(
    dma_id: str,
    service: TelemetryService = Depends()
):
    """Get summary for a DMA"""
    summary = service.get_dma_summary(dma_id)
    if not summary:
        raise NotFoundException("DMA", dma_id)
    return summary


@router.get("/{dma_id}/status")
async def get_dma_status(
    dma_id: str,
    service: TelemetryService = Depends()
):
    """Get current status of a DMA"""
    summary = service.get_dma_summary(dma_id)
    if not summary:
        raise NotFoundException("DMA", dma_id)
    
    return {
        "dma_id": dma_id,
        "dma_name": summary.get("dma_name"),
        "status": summary.get("status"),
        "current_pressure": summary.get("current_reading", {}).pressure_mca if summary.get("current_reading") else None,
        "current_flow": summary.get("current_reading", {}).flow_lps if summary.get("current_reading") else None,
        "last_update": summary.get("current_reading", {}).timestamp if summary.get("current_reading") else None
    }


@router.get("/{dma_id}/sensors")
async def get_dma_sensors(
    dma_id: str,
    service: TelemetryService = Depends()
):
    """Get sensors for a DMA"""
    # Get sensors from provider
    provider = service.provider
    if hasattr(provider, 'sensors'):
        sensors = [s for s in provider.sensors if s["dma_id"] == dma_id]
        return {
            "dma_id": dma_id,
            "sensors": sensors
        }
    
    # Fallback: return basic sensor info
    return {
        "dma_id": dma_id,
        "sensors": [
            {
                "code": f"SENS-{dma_id}-P",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE"
            },
            {
                "code": f"SENS-{dma_id}-F",
                "type": "FLOW",
                "unit": "LPS",
                "status": "ACTIVE"
            }
        ]
    }


@router.get("/moche/sensors")
async def get_moche_sensors(
    service: TelemetryService = Depends()
):
    """Get sensors for Moche sector"""
    return await get_dma_sensors(settings.target_dma, service)


@router.get("/{dma_id}/kpis")
async def get_dma_kpis(
    dma_id: str,
    service: KPIService = Depends()
):
    """Get KPIs for a specific DMA"""
    return service.get_dma_metrics(dma_id)


@router.get("/moche/kpis")
async def get_moche_kpis(
    service: KPIService = Depends()
):
    """Get KPIs for Moche sector"""
    return service.get_dma_metrics(settings.target_dma)