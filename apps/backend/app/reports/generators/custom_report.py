"""Custom Report Generator"""
from datetime import datetime
from typing import Optional
from app.reports.base import BaseReportGenerator, ReportData
from app.services.report_service import ReportService
from app.core.config import settings
from app.services.telemetry_service import TelemetryService


class CustomReportGenerator(BaseReportGenerator):
    """Generator for custom date range reports"""
    
    def __init__(self):
        super().__init__()
        self.report_service = ReportService()
        self.telemetry_service = TelemetryService()
    
    def get_report_type(self) -> str:
        return "custom"
    
    def generate(self, start_date: datetime, end_date: datetime, dma_id: Optional[str] = None) -> ReportData:
        """
        Generate custom date range report
        
        Args:
            start_date: Start date
            end_date: End date
            dma_id: DMA identifier
        
        Returns:
            ReportData with report data
        """
        target_dma = dma_id or settings.target_dma
        
        raw_report = self.report_service.generate_custom_report(start_date, end_date, target_dma)
        
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
                "total_readings": raw_report["statistics"]["total_readings"],
                "avg_pressure": raw_report["statistics"]["avg_pressure"],
                "avg_flow": raw_report["statistics"]["avg_flow"],
                "anomalies_detected": raw_report["statistics"]["anomalies_detected"],
                "incidents_created": raw_report["statistics"]["incidents_created"],
                "incidents_resolved": raw_report["statistics"]["incidents_resolved"],
                "nrw_percentage": raw_report["statistics"]["nrw_percentage"],
                "water_loss_m3": raw_report["statistics"]["water_loss_m3"]
            },
            details={
                "anomalies_list": raw_report.get("anomalies_list", []),
                "incidents_list": raw_report.get("incidents_list", [])
            },
            metadata={
                "report_version": "1.0",
                "generated_by": "SGIP-CAP System",
                "target_dma": target_dma,
                "period_days": (period_end - period_start).days
            }
        )