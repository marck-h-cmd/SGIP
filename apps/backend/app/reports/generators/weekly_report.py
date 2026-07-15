"""Weekly Report Generator"""
from datetime import datetime
from typing import Optional
from app.reports.base import BaseReportGenerator, ReportData
from app.services.report_service import ReportService
from app.core.config import settings
from app.services.telemetry_service import TelemetryService


class WeeklyReportGenerator(BaseReportGenerator):
    """Generator for weekly operational reports"""
    
    def __init__(self):
        super().__init__()
        self.report_service = ReportService()
        self.telemetry_service = TelemetryService()
    
    def get_report_type(self) -> str:
        return "weekly"
    
    def generate(self, end_date: Optional[datetime] = None, dma_id: Optional[str] = None) -> ReportData:
        """
        Generate weekly report
        
        Args:
            end_date: End date for the week (default: today)
            dma_id: DMA identifier
        
        Returns:
            ReportData with report data
        """
        target_dma = dma_id or settings.target_dma
        
        raw_report = self.report_service.generate_weekly_report(end_date)
        
        dma_info = self.telemetry_service.get_dma_info(target_dma)
        dma_name = dma_info.get("name", "Moche 01") if dma_info else "Moche 01"
        
        period_start = datetime.strptime(raw_report["period"]["start"], "%Y-%m-%d")
        period_end = datetime.strptime(raw_report["period"]["end"], "%Y-%m-%d")
        
        return ReportData(
            report_type=self.get_report_type(),
            dma_id=target_dma,
            dma_name=dma_name,
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.utcnow(),
            summary={
                "total_readings": raw_report["total_readings"],
                "total_anomalies": raw_report["total_anomalies"],
                "total_incidents": raw_report["total_incidents"],
                "water_loss_estimate": raw_report["water_loss_estimate"],
                "nrw_percentage": raw_report["nrw_percentage"]
            },
            details={
                "daily_stats": raw_report.get("daily_stats", []),
                "anomaly_trend": raw_report.get("anomaly_trend", {}),
                "incident_trend": raw_report.get("incident_trend", {}),
                "period_days": 7
            },
            metadata={
                "report_version": "1.0",
                "generated_by": "SGIP-CAP System",
                "target_dma": target_dma,
                "period_start": raw_report["period"]["start"],
                "period_end": raw_report["period"]["end"]
            }
        )