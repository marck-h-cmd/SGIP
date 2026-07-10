from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TelemetryReading(BaseModel):
    """Canonical telemetry reading model"""
    id: Optional[int] = None
    timestamp: datetime
    dma_id: str = Field(..., max_length=50)
    dma_name: str = Field(..., max_length=100)
    sensor_id: str = Field(..., max_length=50)
    pressure_mca: float = Field(..., ge=0)
    flow_lps: float = Field(..., ge=0)
    source: str = Field(..., max_length=50)
    quality_flag: str = Field(default="GOOD", max_length=20)
    temperature: Optional[float] = None
    status: str = Field(default="ACTIVE", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "timestamp": "2026-07-09T10:30:00",
                "dma_id": "DMA-EP-01",
                "dma_name": "El Porvenir 01",
                "sensor_id": "SENS-EP-01",
                "pressure_mca": 52.4,
                "flow_lps": 28.6,
                "source": "MOCK",
                "quality_flag": "GOOD"
            }
        }
    )


class TelemetryBatch(BaseModel):
    """Batch of telemetry readings"""
    readings: list[TelemetryReading]
    total_count: int
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)