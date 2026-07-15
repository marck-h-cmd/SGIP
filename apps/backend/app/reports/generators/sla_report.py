"""SLA Report Generator"""
from datetime import datetime
from typing import Optional
from app.reports.base import BaseReportGenerator, ReportData
from app.services.incident_service import IncidentService
from app.core.config import settings
from app.services.telemetry_service import TelemetryService


class SLAReportGenerator(BaseReportGenerator):
    """Generator for SLA performance reports"""
    
    def __init__(self):
        super().__init__()
        self.incident_service = IncidentService()
        self.telemetry_service = TelemetryService()
    
    def get_report_type(self) -> str:
        return "sla"
    
    def generate(self, end_date: Optional[datetime] = None, dma_id: Optional[str] = None) -> ReportData:
        """
        Generate SLA performance report
        
        Args:
            end_date: End date (default: today)
            dma_id: DMA identifier
        
        Returns:
            ReportData with report data
        """
        target_dma = dma_id or settings.target_dma
        
        # Get SLA metrics
        sla_metrics = self.incident_service.get_sla_metrics(target_dma)
        
        # Get all incidents for the DMA
        incidents = self.incident_service.get_all_tickets(dma_id=target_dma, limit=500)
        
        dma_info = self.telemetry_service.get_dma_info(target_dma)
        dma_name = dma_info.get("name", "Moche 01") if dma_info else "Moche 01"
        
        # Calculate breach statistics
        breached_incidents = [i for i in incidents if i.sla_due_date and i.sla_due_date < datetime.utcnow()]
        in_progress_incidents = [i for i in incidents if i.status.value == "IN_PROGRESS"]
        resolved_incidents = [i for i in incidents if i.status.value in ["RESOLVED", "CLOSED"]]
        
        # Calculate response times
        response_times = []
        for i in incidents:
            if i.resolved_at and i.created_at:
                response_time = (i.resolved_at - i.created_at).total_seconds() / 3600
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return ReportData(
            report_type=self.get_report_type(),
            dma_id=target_dma,
            dma_name=dma_name,
            period_start=datetime.utcnow().replace(day=1, hour=0, minute=0, second=0),
            period_end=datetime.utcnow(),
            generated_at=datetime.utcnow(),
            summary={
                "total_incidents": sla_metrics.get("total_incidents", 0),
                "breached_incidents": sla_metrics.get("breached_incidents", 0),
                "breach_rate": sla_metrics.get("breach_rate", 0),
                "avg_response_hours": sla_metrics.get("avg_response_hours", 0),
                "resolved_count": len(resolved_incidents),
                "in_progress_count": len(in_progress_incidents),
                "avg_resolution_time_hours": round(avg_response_time, 2)
            },
            details={
                "by_priority": sla_metrics.get("by_priority", {}),
                "by_status": sla_metrics.get("by_status", {}),
                "breached_incidents": [{
                    "code": i.code,
                    "title": i.title,
                    "priority": i.priority.value,
                    "created_at": i.created_at.isoformat() if i.created_at else "",
                    "sla_due_date": i.sla_due_date.isoformat() if i.sla_due_date else ""
                } for i in breached_incidents[:20]],
                "top_response_times": sorted(response_times, reverse=True)[:10]
            },
            metadata={
                "report_version": "1.0",
                "generated_by": "SGIP-CAP System",
                "target_dma": target_dma
            }
        )