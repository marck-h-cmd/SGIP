from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TelemetryResponse(BaseModel):
    """Response schema for telemetry data"""
    id: Optional[int] = None
    timestamp: datetime
    dma_id: str
    dma_name: str
    sensor_id: str
    pressure_mca: float
    flow_lps: float
    source: str
    quality_flag: str
    temperature: Optional[float] = None
    status: str = "ACTIVE"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TelemetryHistoryResponse(BaseModel):
    """Response schema for historical telemetry"""
    dma_id: str
    dma_name: str
    readings: List[TelemetryResponse]
    total_count: int
    start_date: datetime
    end_date: datetime


class TelemetryFilter(BaseModel):
    """Filter for telemetry queries"""
    dma_id: Optional[str] = None
    sensor_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class TelemetrySummary(BaseModel):
    """Summary statistics for telemetry"""
    dma_id: str
    dma_name: str
    current_pressure: Optional[float] = None
    current_flow: Optional[float] = None
    avg_pressure_24h: Optional[float] = None
    avg_flow_24h: Optional[float] = None
    max_pressure_24h: Optional[float] = None
    min_pressure_24h: Optional[float] = None
    max_flow_24h: Optional[float] = None
    min_flow_24h: Optional[float] = None
    sample_count_24h: int = 0
    last_update: datetime