from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.services.incident_service import IncidentService
from app.services.anomaly_service import AnomalyService
from app.domain.incident import IncidentStatus, IncidentPriority
from app.schemas.incident_schema import (
    IncidentCreate, IncidentUpdate, IncidentResponse,
    IncidentCommentCreate, IncidentAuditLogResponse
)
from app.core.exceptions import NotFoundException, ValidationException
from app.api.dependencies import get_incident_service, get_anomaly_service

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/create")
async def create_incident(
    incident_data: IncidentCreate,
    incident_service: IncidentService = Depends(get_incident_service),
    anomaly_service: AnomalyService = Depends(get_anomaly_service)
):
    """Create an incident from an anomaly"""
    anomalies = anomaly_service.get_recent_anomalies(hours=168)
    anomaly = None
    for a in anomalies:
        if a.get("anomaly") and a["anomaly"].id == incident_data.anomaly_id:
            anomaly = a["anomaly"]
            break
    
    if not anomaly:
        raise NotFoundException("Anomaly", str(incident_data.anomaly_id))
    
    ticket = incident_service.create_incident(anomaly)
    return IncidentResponse(**ticket.dict())


@router.post("/create-from-anomaly/{anomaly_id}")
async def create_incident_from_anomaly(
    anomaly_id: int,
    incident_service: IncidentService = Depends(get_incident_service),
    anomaly_service: AnomalyService = Depends(get_anomaly_service)
):
    """Create an incident directly from an anomaly ID"""
    anomalies = anomaly_service.get_recent_anomalies(hours=168)
    anomaly = None
    for a in anomalies:
        if a.get("anomaly") and a["anomaly"].id == anomaly_id:
            anomaly = a["anomaly"]
            break
    
    if not anomaly:
        raise NotFoundException("Anomaly", str(anomaly_id))
    
    ticket = incident_service.create_incident(anomaly)
    return IncidentResponse(**ticket.dict())


@router.get("/")
async def get_incidents(
    status: Optional[IncidentStatus] = Query(None),
    dma_id: Optional[str] = Query(None),
    priority: Optional[IncidentPriority] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    service: IncidentService = Depends(get_incident_service)
):
    """Get incidents with filters and pagination"""
    tickets = service.get_all_tickets(status, dma_id, priority, limit, offset)
    return [IncidentResponse(**t.dict()) for t in tickets]


@router.get("/moche")
async def get_moche_incidents(
    status: Optional[IncidentStatus] = Query(None),
    priority: Optional[IncidentPriority] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    service: IncidentService = Depends(get_incident_service)
):
    """Get incidents for Moche sector"""
    from app.core.config import settings
    tickets = service.get_all_tickets(status, settings.target_dma, priority, limit, offset)
    return {
        "sector": "Moche",
        "total": len(tickets),
        "incidents": [IncidentResponse(**t.dict()) for t in tickets]
    }


@router.get("/{ticket_id}")
async def get_incident(
    ticket_id: int,
    service: IncidentService = Depends(get_incident_service)
):
    """Get a specific incident"""
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket", str(ticket_id))
    return IncidentResponse(**ticket.dict())


@router.get("/code/{code}")
async def get_incident_by_code(
    code: str,
    service: IncidentService = Depends(get_incident_service)
):
    """Get an incident by its code"""
    ticket = service.get_ticket_by_code(code)
    if not ticket:
        raise NotFoundException("Ticket", code)
    return IncidentResponse(**ticket.dict())


@router.patch("/{ticket_id}/status")
async def update_incident_status(
    ticket_id: int,
    status: IncidentStatus,
    notes: Optional[str] = None,
    user: str = "operator",
    service: IncidentService = Depends(get_incident_service)
):
    """Update incident status with ITIL validation"""
    try:
        ticket = service.update_ticket_status(ticket_id, status, user, notes)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/assign")
async def assign_incident(
    ticket_id: int,
    assigned_to: str,
    user: str = "operator",
    service: IncidentService = Depends(get_incident_service)
):
    """Assign an incident to someone"""
    try:
        ticket = service.assign_ticket(ticket_id, assigned_to, user)
        return IncidentResponse(**ticket.dict())
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/comment")
async def add_incident_comment(
    ticket_id: int,
    comment_data: IncidentCommentCreate,
    service: IncidentService = Depends(get_incident_service)
):
    """Add comment to incident"""
    try:
        ticket = service.add_comment(ticket_id, comment_data.user, comment_data.comment, comment_data.is_internal)
        return IncidentResponse(**ticket.dict())
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/escalate")
async def escalate_incident(
    ticket_id: int,
    reason: str = "SLA breach imminent",
    user: str = "system",
    service: IncidentService = Depends(get_incident_service)
):
    """Escalate an incident"""
    try:
        ticket = service.escalate_ticket(ticket_id, user, reason)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/link-anomaly")
async def link_anomaly_to_incident(
    ticket_id: int,
    anomaly_id: int,
    service: IncidentService = Depends(get_incident_service)
):
    """Link an anomaly to an incident"""
    try:
        ticket = service.link_anomaly(ticket_id, anomaly_id)
        return IncidentResponse(**ticket.dict())
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/{ticket_id}/audit-log")
async def get_incident_audit_log(
    ticket_id: int,
    service: IncidentService = Depends(get_incident_service)
):
    """Get audit log for an incident"""
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket", str(ticket_id))
    
    logs = service.get_ticket_audit_log(ticket_id)
    return [IncidentAuditLogResponse(**log) for log in logs]


@router.post("/{ticket_id}/resolve")
async def resolve_incident(
    ticket_id: int,
    resolution_notes: Optional[str] = None,
    user: str = "operator",
    service: IncidentService = Depends(get_incident_service)
):
    """Resolve an incident"""
    try:
        ticket = service.update_ticket_status(ticket_id, IncidentStatus.RESOLVED, user, resolution_notes)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/close")
async def close_incident(
    ticket_id: int,
    user: str = "operator",
    service: IncidentService = Depends(get_incident_service)
):
    """Close an incident"""
    try:
        ticket = service.update_ticket_status(ticket_id, IncidentStatus.CLOSED, user)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/check-sla-breaches")
async def check_sla_breaches(
    service: IncidentService = Depends(get_incident_service)
):
    """Check and escalate SLA breaches (for cron job)"""
    escalated = service.check_and_escalate_sla_breaches()
    return {
        "checked_at": datetime.utcnow().isoformat(),
        "escalated_count": len(escalated),
        "escalated": [IncidentResponse(**t.dict()) for t in escalated]
    }


@router.get("/sla/metrics")
async def get_sla_metrics(
    service: IncidentService = Depends(get_incident_service)
):
    """Get SLA metrics"""
    return service.get_sla_metrics()


@router.get("/moche/sla-metrics")
async def get_moche_sla_metrics(
    service: IncidentService = Depends(get_incident_service)
):
    """Get SLA metrics for Moche sector"""
    metrics = service.get_sla_metrics()
    from app.core.config import settings
    
    tickets = service.get_all_tickets(dma_id=settings.target_dma)
    moche_metrics = {
        **metrics,
        "sector": "Moche",
        "moche_tickets": len(tickets),
        "moche_open": len([t for t in tickets if t.status.value not in ["CLOSED", "RESOLVED"]])
    }
    return moche_metrics