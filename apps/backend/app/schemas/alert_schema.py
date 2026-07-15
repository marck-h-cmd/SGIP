from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AlertResponse(BaseModel):
    """Response schema for alerts"""
    id: int
    type: str
    severity: str
    title: str
    message: str
    dma_id: str
    dma_name: str
    anomaly_id: Optional[int] = None
    incident_id: Optional[int] = None
    timestamp: str
    status: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved: bool
    resolved_at: Optional[str] = None


class AlertSummary(BaseModel):
    """Summary of alerts"""
    total_active: int
    critical: int
    high: int
    medium: int
    low: int
    last_alert: Optional[AlertResponse] = None