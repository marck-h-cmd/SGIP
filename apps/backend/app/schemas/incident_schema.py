from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.domain.incident import IncidentPriority, IncidentStatus


class IncidentCreate(BaseModel):
    """Schema for creating an incident"""
    anomaly_id: int
    dma_id: str
    title: str
    description: str
    priority: IncidentPriority
    assigned_to: Optional[str] = None
    sla_due_at: datetime


class IncidentUpdate(BaseModel):
    """Schema for updating an incident"""
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[str] = None
    priority: Optional[IncidentPriority] = None
    description: Optional[str] = None
    resolution_notes: Optional[str] = None


class IncidentResponse(BaseModel):
    """Response schema for incidents"""
    id: int
    code: str
    anomaly_id: int
    dma_id: str
    dma_name: str
    title: str
    description: str
    priority: IncidentPriority
    status: IncidentStatus
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sla_due_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    is_sla_breached: bool = False