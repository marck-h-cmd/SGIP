from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any


class DailyReportResponse(BaseModel):
    """Response schema for daily reports"""
    date: str
    dma: dict
    summary: dict
    anomalies: dict
    incidents: dict
    generated_at: str


class WeeklyReportResponse(BaseModel):
    """Response schema for weekly reports"""
    period: dict
    dma: str
    daily_stats: List[dict]
    total_anomalies: int
    total_incidents: int
    anomaly_trend: dict
    incident_trend: dict
    generated_at: str