"""Daily Report Generator"""
from datetime import datetime, timedelta
from typing import Optional
from app.reports.base import BaseReportGenerator, ReportData
from app.services.report_service import ReportService
from app.core.config import settings
from app.services.telemetry_service import TelemetryService


class DailyReportGenerator(BaseReportGenerator):
    """Generator for daily operational reports"""
    
    def __init__(self):
        super().__init__()
        self.report_service = ReportService()
        self.telemetry_service = TelemetryService()
    
    def get_report_type(self) -> str:
        return "daily"
    
    def generate(self, date: Optional[datetime] = None, dma_id: Optional[str] = None) -> ReportData:
        """
        Generate daily report
        
        Args:
            date: Date for the report (default: today in Peru timezone)
            dma_id: DMA identifier (default: from settings)
        
        Returns:
            ReportData with report data
        """
        target_dma = dma_id or settings.target_dma
        
        # Get raw report data
        raw_report = self.report_service.generate_daily_report(date)
        
        # Get DMA info
        dma_info = self.telemetry_service.get_dma_info(target_dma)
        dma_name = dma_info.get("name", "Moche 01") if dma_info else "Moche 01"
        
        # Parse date
        report_date = datetime.strptime(raw_report["date"], "%Y-%m-%d")
        
        return ReportData(
            report_type=self.get_report_type(),
            dma_id=target_dma,
            dma_name=dma_name,
            period_start=report_date.replace(hour=0, minute=0, second=0),
            period_end=report_date.replace(hour=23, minute=59, second=59),
            generated_at=datetime.utcnow(),
            summary={
                "total_readings": raw_report["summary"]["total_readings"],
                "avg_pressure": raw_report["summary"]["avg_pressure"],
                "avg_flow": raw_report["summary"]["avg_flow"],
                "nrw_percentage": raw_report["summary"]["nrw_percentage"],
                "water_loss_m3": raw_report["summary"]["water_loss_m3"],
                "anomalies_total": raw_report["anomalies"]["total"],
                "anomalies_critical": raw_report["anomalies"]["critical"],
                "incidents_total": raw_report["incidents"]["total"],
                "incidents_open": raw_report["incidents"]["open"]
            },
            details={
                "readings": raw_report.get("readings", []),
                "anomalies_breakdown": raw_report["anomalies"],
                "incidents_breakdown": raw_report["incidents"],
                "pressure_stats": {
                    "min": raw_report["summary"]["min_pressure"],
                    "max": raw_report["summary"]["max_pressure"]
                },
                "flow_stats": {
                    "min": raw_report["summary"]["min_flow"],
                    "max": raw_report["summary"]["max_flow"]
                }
            },
            metadata={
                "report_version": "1.0",
                "generated_by": "SGIP-CAP System",
                "target_dma": target_dma,
                "report_date": raw_report["date"]
            }
        )