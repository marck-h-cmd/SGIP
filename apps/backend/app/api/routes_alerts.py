from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.services.alert_service import AlertService
from app.schemas.alert_schema import AlertResponse, AlertSummary
from app.api.dependencies import get_alert_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/")
async def get_alerts(
    active_only: bool = False,
    service: AlertService = Depends(get_alert_service)
) -> List[AlertResponse]:
    """Get all alerts"""
    if active_only:
        alerts = service.get_active_alerts()
    else:
        alerts = service.alerts
    
    return [AlertResponse(**a) for a in alerts]


@router.get("/{dma_id}")
async def get_alerts_by_dma(
    dma_id: str,
    service: AlertService = Depends(get_alert_service)
) -> List[AlertResponse]:
    """Get alerts for a specific DMA"""
    alerts = service.get_alerts_by_dma(dma_id)
    return [AlertResponse(**a) for a in alerts]


@router.get("/summary")
async def get_alert_summary(
    service: AlertService = Depends(get_alert_service)
) -> AlertSummary:
    """Get alert summary"""
    summary = service.get_alert_summary()
    return AlertSummary(**summary)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    user: str,
    service: AlertService = Depends(get_alert_service)
) -> AlertResponse:
    """Acknowledge an alert"""
    alert = service.acknowledge_alert(alert_id, user)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    service: AlertService = Depends(get_alert_service)
) -> AlertResponse:
    """Resolve an alert"""
    alert = service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse(**alert)


@router.get("/history")
async def get_alert_history(
    hours: int = 24,
    service: AlertService = Depends(get_alert_service)
) -> List[AlertResponse]:
    """Get alert history"""
    alerts = service.get_alert_history(hours)
    return [AlertResponse(**a) for a in alerts]