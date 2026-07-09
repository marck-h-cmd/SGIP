from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from datetime import datetime
from app.services.incident_service import IncidentService
from app.services.anomaly_service import AnomalyService
from app.domain.incident import IncidentStatus, IncidentPriority
from app.schemas.incident_schema import IncidentCreate, IncidentUpdate, IncidentResponse
from app.core.exceptions import NotFoundException, ValidationException

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/create")
async def create_incident(
    incident_data: IncidentCreate,
    incident_service: IncidentService = Depends(),
    anomaly_service: AnomalyService = Depends()
):
    """Create an incident from an anomaly"""
    # Get anomaly
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
    incident_service: IncidentService = Depends(),
    anomaly_service: AnomalyService = Depends()
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
    service: IncidentService = Depends()
):
    """Get incidents with filters"""
    tickets = service.get_all_tickets(status, dma_id, priority, limit, offset)
    return [IncidentResponse(**t.dict()) for t in tickets]


@router.get("/moche")
async def get_moche_incidents(
    status: Optional[IncidentStatus] = Query(None),
    priority: Optional[IncidentPriority] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    service: IncidentService = Depends()
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
    service: IncidentService = Depends()
):
    """Get a specific incident"""
    ticket = service.get_ticket(ticket_id)
    if not ticket:
        raise NotFoundException("Ticket", str(ticket_id))
    return IncidentResponse(**ticket.dict())


@router.get("/code/{code}")
async def get_incident_by_code(
    code: str,
    service: IncidentService = Depends()
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
    service: IncidentService = Depends()
):
    """Update incident status"""
    try:
        ticket = service.update_ticket_status(ticket_id, status, notes)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/assign")
async def assign_incident(
    ticket_id: int,
    assigned_to: str,
    service: IncidentService = Depends()
):
    """Assign an incident to someone"""
    try:
        ticket = service.assign_ticket(ticket_id, assigned_to)
        return IncidentResponse(**ticket.dict())
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/resolve")
async def resolve_incident(
    ticket_id: int,
    resolution_notes: Optional[str] = None,
    service: IncidentService = Depends()
):
    """Resolve an incident"""
    try:
        ticket = service.update_ticket_status(ticket_id, IncidentStatus.RESOLVED, resolution_notes)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/{ticket_id}/close")
async def close_incident(
    ticket_id: int,
    service: IncidentService = Depends()
):
    """Close an incident"""
    try:
        ticket = service.update_ticket_status(ticket_id, IncidentStatus.CLOSED)
        return IncidentResponse(**ticket.dict())
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/sla/metrics")
async def get_sla_metrics(
    service: IncidentService = Depends()
):
    """Get SLA metrics"""
    return service.get_sla_metrics()


@router.get("/moche/sla-metrics")
async def get_moche_sla_metrics(
    service: IncidentService = Depends()
):
    """Get SLA metrics for Moche sector"""
    metrics = service.get_sla_metrics()
    from app.core.config import settings
    
    # Get tickets for Moche
    tickets = service.get_all_tickets(dma_id=settings.target_dma)
    moche_metrics = {
        **metrics,
        "sector": "Moche",
        "moche_tickets": len(tickets),
        "moche_open": len([t for t in tickets if t.status.value not in ["CLOSED", "RESOLVED"]])
    }
    return moche_metrics