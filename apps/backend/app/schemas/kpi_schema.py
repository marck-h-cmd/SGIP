from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ExecutiveKPI(BaseModel):
    """Executive dashboard KPIs"""
    total_dmas_monitored: int
    active_dmas: int
    total_incidents_today: int
    active_incidents: int
    critical_incidents: int
    sla_compliance_rate: float
    average_detection_time_minutes: float
    average_resolution_time_minutes: float
    estimated_water_loss_saved: float  # in cubic meters
    anomaly_detection_rate: float
    dmas_at_risk: int
    last_updated: datetime


class DMAMetrics(BaseModel):
    """Metrics for a specific DMA"""
    dma_id: str
    dma_name: str
    current_pressure: Optional[float] = None
    current_flow: Optional[float] = None
    pressure_anomaly_score: float
    flow_anomaly_score: float
    incidents_last_30_days: int
    average_response_time: float
    water_loss_estimate: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class TimeSeriesMetric(BaseModel):
    """Time series data for charts"""
    timestamp: datetime
    value: float
    metric_type: str  # PRESSURE, FLOW, ANOMALY_SCORE, etc.
    dma_id: str
    dma_name: str
    unit: str