from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.telemetry_service import TelemetryService
from app.services.anomaly_service import AnomalyService
from app.services.incident_service import IncidentService
from app.services.kpi_service import KPIService
from app.core.config import settings


class ReportService:
    """Service for generating reports"""
    
    def __init__(self):
        self.telemetry_service = TelemetryService()
        self.anomaly_service = AnomalyService()
        self.incident_service = IncidentService()
        self.kpi_service = KPIService()
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily operational report"""
        if date is None:
            date = datetime.utcnow()
        
        date_str = date.strftime("%Y-%m-%d")
        
        # Get data for the day
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Get DMA info
        dma_info = self.telemetry_service.get_dma_info(settings.target_dma)
        
        # Get readings for the day
        readings = self.telemetry_service.get_historical_readings(
            settings.target_dma,
            start_date,
            end_date,
            limit=10000
        )
        
        # Get anomalies for the day
        anomalies = self.anomaly_service.get_recent_anomalies(
            settings.target_dma,
            hours=24
        )
        
        # Get incidents for the day
        incidents = self.incident_service.get_all_tickets(
            dma_id=settings.target_dma,
            limit=100
        )
        
        # Calculate statistics
        avg_pressure = sum(r.pressure_mca for r in readings) / len(readings) if readings else 0
        avg_flow = sum(r.flow_lps for r in readings) / len(readings) if readings else 0
        
        return {
            "date": date_str,
            "dma": {
                "code": settings.target_dma,
                "name": dma_info.get("name", "Moche 01") if dma_info else "Moche 01",
                "district": dma_info.get("district", "Moche") if dma_info else "Moche"
            },
            "summary": {
                "total_readings": len(readings),
                "avg_pressure": round(avg_pressure, 1),
                "avg_flow": round(avg_flow, 1),
                "max_pressure": max([r.pressure_mca for r in readings]) if readings else 0,
                "min_pressure": min([r.pressure_mca for r in readings]) if readings else 0,
                "max_flow": max([r.flow_lps for r in readings]) if readings else 0,
                "min_flow": min([r.flow_lps for r in readings]) if readings else 0
            },
            "anomalies": {
                "total": len(anomalies),
                "critical": len([a for a in anomalies if a.get("severity") == "CRITICAL"]),
                "high": len([a for a in anomalies if a.get("severity") == "HIGH"])
            },
            "incidents": {
                "total": len(incidents),
                "open": len([i for i in incidents if i.status.value not in ["CLOSED", "RESOLVED"]]),
                "resolved": len([i for i in incidents if i.status.value in ["RESOLVED", "CLOSED"]])
            },
            "readings": [{"timestamp": r.timestamp.isoformat(), "pressure_mca": r.pressure_mca, "flow_lps": r.flow_lps, "is_anomaly": False} for r in readings],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Get data for the week
        readings = self.telemetry_service.get_historical_readings(
            settings.target_dma,
            start_date,
            end_date,
            limit=10000
        )
        
        anomalies = self.anomaly_service.get_recent_anomalies(
            settings.target_dma,
            hours=168  # 7 days
        )
        
        incidents = self.incident_service.get_all_tickets(
            dma_id=settings.target_dma
        )
        
        # Calculate daily averages
        daily_stats = []
        current = start_date
        while current <= end_date:
            day_end = current + timedelta(days=1)
            day_readings = [r for r in readings if current <= r.timestamp < day_end]
            
            if day_readings:
                daily_stats.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "avg_pressure": round(sum(r.pressure_mca for r in day_readings) / len(day_readings), 1),
                    "avg_flow": round(sum(r.flow_lps for r in day_readings) / len(day_readings), 1),
                    "readings_count": len(day_readings)
                })
            
            current = day_end
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "dma": settings.target_dma,
            "daily_stats": daily_stats,
            "total_readings": len(readings),
            "total_anomalies": len(anomalies),
            "total_incidents": len(incidents),
            "water_loss_estimate": round(sum(a.get("anomaly").estimated_loss_volume for a in anomalies if a.get("anomaly") and a.get("anomaly").estimated_loss_volume), 2),
            "anomaly_trend": self._calculate_trend(anomalies),
            "incident_trend": self._calculate_incident_trend(incidents),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_trend(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """Calculate anomaly trend"""
        if not anomalies:
            return {"trend": "STABLE", "change_percentage": 0}
        
        # Group by day
        daily_counts = {}
        for item in anomalies:
            anomaly = item.get("anomaly")
            if anomaly and anomaly.detected_at:
                date = anomaly.detected_at.strftime("%Y-%m-%d")
                daily_counts[date] = daily_counts.get(date, 0) + 1
        
        if len(daily_counts) < 2:
            return {"trend": "STABLE", "change_percentage": 0}
        
        # Compare last two days
        dates = sorted(daily_counts.keys())
        last_day = dates[-1]
        prev_day = dates[-2]
        
        current = daily_counts.get(last_day, 0)
        previous = daily_counts.get(prev_day, 0)
        
        if previous == 0:
            change_pct = 100 if current > 0 else 0
        else:
            change_pct = ((current - previous) / previous) * 100
        
        trend = "RISING" if change_pct > 10 else "FALLING" if change_pct < -10 else "STABLE"
        
        return {
            "trend": trend,
            "change_percentage": round(change_pct, 1),
            "current_count": current,
            "previous_count": previous
        }
    
    def _calculate_incident_trend(self, incidents: List) -> Dict[str, Any]:
        """Calculate incident trend"""
        if not incidents:
            return {"trend": "STABLE", "change_percentage": 0}
        
        # Similar logic as above
        daily_counts = {}
        for incident in incidents:
            date = incident.created_at.strftime("%Y-%m-%d")
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        if len(daily_counts) < 2:
            return {"trend": "STABLE", "change_percentage": 0}
        
        dates = sorted(daily_counts.keys())
        last_day = dates[-1]
        prev_day = dates[-2]
        
        current = daily_counts.get(last_day, 0)
        previous = daily_counts.get(prev_day, 0)
        
        if previous == 0:
            change_pct = 100 if current > 0 else 0
        else:
            change_pct = ((current - previous) / previous) * 100
        
        trend = "RISING" if change_pct > 10 else "FALLING" if change_pct < -10 else "STABLE"
        
        return {
            "trend": trend,
            "change_percentage": round(change_pct, 1),
            "current_count": current,
            "previous_count": previous
        }