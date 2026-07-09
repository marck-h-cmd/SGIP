from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.kpi_service import KPIService
from app.core.config import settings

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("/executive")
async def get_executive_kpis(
    service: KPIService = Depends()
):
    """Get executive dashboard KPIs"""
    return service.get_executive_kpis()


@router.get("/moche/executive")
async def get_moche_executive_kpis(
    service: KPIService = Depends()
):
    """Get executive dashboard KPIs focused on Moche"""
    kpis = service.get_executive_kpis()
    # Add Moche-specific metrics
    moche_metrics = service.get_dma_metrics(settings.target_dma)
    
    return {
        **kpis,
        "sector": "Moche",
        "sector_metrics": moche_metrics
    }


@router.get("/dma/{dma_id}")
async def get_dma_metrics(
    dma_id: str,
    service: KPIService = Depends()
):
    """Get metrics for a specific DMA"""
    return service.get_dma_metrics(dma_id)


@router.get("/moche/metrics")
async def get_moche_metrics(
    service: KPIService = Depends()
):
    """Get metrics specifically for Moche sector"""
    return service.get_dma_metrics(settings.target_dma)


@router.get("/dmas/all")
async def get_all_dma_metrics(
    service: KPIService = Depends()
):
    """Get metrics for all DMAs"""
    dmas = service.telemetry_service.get_all_dmas()
    metrics = []
    for dma in dmas:
        metric = service.get_dma_metrics(dma["code"])
        if "error" not in metric:
            metrics.append(metric)
    return metrics


@router.get("/water-loss")
async def get_water_loss_metrics(
    dma_id: Optional[str] = Query(None, description="Filter by DMA ID"),
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    service: KPIService = Depends()
):
    """Get water loss metrics"""
    if dma_id:
        metrics = service.get_dma_metrics(dma_id)
        return {
            "dma_id": dma_id,
            "estimated_loss": metrics.get("water_loss_estimate", 0),
            "risk_level": metrics.get("risk_level", "UNKNOWN")
        }
    else:
        # Get all DMAs
        dmas = service.telemetry_service.get_all_dmas()
        total_loss = 0
        for dma in dmas:
            metrics = service.get_dma_metrics(dma["code"])
            if "error" not in metrics:
                total_loss += metrics.get("water_loss_estimate", 0)
        
        return {
            "total_estimated_loss": total_loss,
            "dmas_analyzed": len(dmas)
        }


@router.get("/moche/water-loss")
async def get_moche_water_loss(
    days: int = Query(30, ge=1, le=365, description="Days to analyze"),
    service: KPIService = Depends()
):
    """Get water loss metrics for Moche sector"""
    metrics = service.get_dma_metrics(settings.target_dma)
    return {
        "sector": "Moche",
        "estimated_loss_daily": metrics.get("water_loss_estimate", 0),
        "estimated_loss_monthly": metrics.get("water_loss_estimate", 0) * 30,
        "risk_level": metrics.get("risk_level", "UNKNOWN"),
        "incidents_last_30_days": metrics.get("incidents_last_30_days", 0),
        "average_response_time": metrics.get("average_response_time", 0)
    }


@router.get("/sla-compliance")
async def get_sla_compliance(
    service: KPIService = Depends()
):
    """Get SLA compliance metrics"""
    from app.services.incident_service import IncidentService
    incident_service = IncidentService()
    return incident_service.get_sla_metrics()


@router.get("/moche/sla-compliance")
async def get_moche_sla_compliance(
    service: KPIService = Depends()
):
    """Get SLA compliance metrics for Moche sector"""
    from app.services.incident_service import IncidentService
    incident_service = IncidentService()
    metrics = incident_service.get_sla_metrics()
    
    # Filter for Moche
    tickets = incident_service.get_all_tickets(dma_id=settings.target_dma)
    moche_breached = len([t for t in tickets if datetime.utcnow() > t.sla_due_at])
    
    return {
        **metrics,
        "sector": "Moche",
        "moche_sla_compliance": 1 - (moche_breached / len(tickets)) if tickets else 1.0,
        "moche_tickets": len(tickets),
        "moche_breached": moche_breached
    }