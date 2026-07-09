from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class Anomaly(BaseModel):
    """Anomaly domain model"""
    id: Optional[int] = None
    telemetry_id: int
    dma_id: str = Field(..., max_length=50)
    dma_name: str = Field(..., max_length=100)
    anomaly_score: float = Field(..., ge=0, le=1)
    severity: AnomalySeverity
    status: AnomalyStatus = Field(default=AnomalyStatus.PENDING)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    pressure_variation: Optional[float] = None
    flow_variation: Optional[float] = None
    estimated_loss_volume: Optional[float] = None
    description: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "telemetry_id": 1,
                "dma_id": "DMA-EP-01",
                "dma_name": "El Porvenir 01",
                "anomaly_score": 0.94,
                "severity": "CRITICAL",
                "status": "PENDING",
                "pressure_variation": -8.5,
                "flow_variation": 12.3,
                "estimated_loss_volume": 45.6
            }
        }