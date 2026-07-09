from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Sensor(BaseModel):
    """Sensor domain model"""
    id: Optional[int] = None
    code: str = Field(..., max_length=50)
    dma_id: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=20)  # PRESSURE, FLOW, TEMPERATURE
    unit: str = Field(..., max_length=10)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = Field(default="ACTIVE", max_length=20)
    last_calibration: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "SENS-EP-01",
                "dma_id": "DMA-EP-01",
                "name": "Pressure Sensor El Porvenir",
                "type": "PRESSURE",
                "unit": "MCA",
                "status": "ACTIVE"
            }
        }