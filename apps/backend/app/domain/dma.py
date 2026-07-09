from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DMA(BaseModel):
    """DMA (District Metered Area) domain model"""
    id: Optional[int] = None
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    district: str = Field(..., max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = Field(default="ACTIVE", max_length=20)
    description: Optional[str] = None
    population_served: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "DMA-EP-01",
                "name": "El Porvenir 01",
                "district": "El Porvenir",
                "latitude": -8.0809,
                "longitude": -79.0039,
                "status": "ACTIVE"
            }
        }


class DMAStatus(BaseModel):
    """DMA status with metrics"""
    dma: DMA
    current_pressure: Optional[float] = None
    current_flow: Optional[float] = None
    pressure_trend: str = "STABLE"  # STABLE, RISING, FALLING
    flow_trend: str = "STABLE"
    anomaly_score: Optional[float] = None
    status_color: str = "GREEN"  # GREEN, YELLOW, RED
    active_incidents: int = 0
    last_reading_time: Optional[datetime] = None