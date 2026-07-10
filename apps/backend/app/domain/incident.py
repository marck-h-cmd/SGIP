from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class IncidentPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    NEW = "NEW"
    CLASSIFIED = "CLASSIFIED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    REOPENED = "REOPENED"


class IncidentTicket(BaseModel):
    """ITIL Incident ticket model"""
    id: Optional[int] = None
    code: str = Field(..., max_length=20)
    anomaly_id: int
    dma_id: str = Field(..., max_length=50)
    dma_name: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: str
    priority: IncidentPriority
    status: IncidentStatus = Field(default=IncidentStatus.NEW)
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    sla_due_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    response_time_minutes: Optional[int] = None
    resolution_time_minutes: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True, json_schema_extra={
            "example": {
                "code": "INC-20260709-001",
                "anomaly_id": 1,
                "dma_id": "DMA-EP-01",
                "dma_name": "El Porvenir 01",
                "title": "Fuga detectada en El Porvenir 01",
                "description": "Presión anormalmente baja con incremento de caudal",
                "priority": "CRITICAL",
                "status": "NEW",
                "assigned_to": "operador@sedalib.pe",
                "sla_due_at": "2026-07-09T14:30:00"
            }
        }
    )
