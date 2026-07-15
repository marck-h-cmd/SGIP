from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.telemetry_service import TelemetryService
from app.services.anomaly_service import AnomalyService
from app.services.incident_service import IncidentService
from app.core.config import settings
from app.infrastructure.database import db


# Perú timezone (UTC-5)
from datetime import timezone
PERU_TZ = timezone(timedelta(hours=-5))


class ReportService:
    """Service for generating operational reports with proper date filtering and NRW calculation"""

    def __init__(self):
        self.telemetry_service = TelemetryService()
        self.anomaly_service = AnomalyService()
        self.incident_service = IncidentService()
        self._db = db

    def _now_peru(self) -> datetime:
        """Get current time in Peru timezone"""
        return datetime.now(PERU_TZ)

    def _peru_day_bounds(self, date: datetime) -> tuple:
        """Get UTC start and end of day in Peru timezone"""
        if date.tzinfo is None:
            date = date.replace(tzinfo=PERU_TZ)
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    def _peru_week_bounds(self, end_date: datetime = None) -> tuple:
        """Get UTC start and end of week (Monday-Sunday) in Peru timezone"""
        if end_date is None:
            end_date = self._now_peru()
        elif end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=PERU_TZ)
        
        # Find Monday of this week
        days_since_monday = end_date.weekday()
        start = end_date - timedelta(days=days_since_monday)
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7)
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily operational report with proper date filtering"""
        if date is None:
            date = self._now_peru()
        
        date_str = date.strftime("%Y-%m-%d")
        start_utc, end_utc = self._peru_day_bounds(date)

        # Get DMA info
        dma_info = self.telemetry_service.get_dma_info(settings.target_dma)

        # Get readings for the specific day (UTC bounds)
        readings = self.telemetry_service.get_historical_readings(
            settings.target_dma,
            start_utc,
            end_utc,
            limit=10000
        )

        # Get anomalies for the day
        anomalies = self.anomaly_service.get_recent_anomalies(
            settings.target_dma,
            hours=24
        )
        # Filter anomalies to the specific day
        day_anomalies = [
            a for a in anomalies 
            if a.get("anomaly") and a["anomaly"].detected_at and 
            start_utc <= a["anomaly"].detected_at.replace(tzinfo=timezone.utc) < end_utc
        ]

        # Get incidents created on this day
        incidents = self.incident_service.get_all_tickets(
            dma_id=settings.target_dma,
            limit=500
        )
        day_incidents = [
            i for i in incidents
            if i.created_at and start_utc <= i.created_at.replace(tzinfo=timezone.utc) < end_utc
        ]

        # Calculate statistics
        avg_pressure = sum(r.pressure_mca for r in readings) / len(readings) if readings else 0
        avg_flow = sum(r.flow_lps for r in readings) / len(readings) if readings else 0
        max_pressure = max([r.pressure_mca for r in readings]) if readings else 0
        min_pressure = min([r.pressure_mca for r in readings]) if readings else 0
        max_flow = max([r.flow_lps for r in readings]) if readings else 0
        min_flow = min([r.flow_lps for r in readings]) if readings else 0

        # NRW Calculation (Non-Revenue Water %)
        # NRW = (System Input - Billed Authorized Consumption) / System Input * 100
        # For MVP: estimate based on anomaly flow excess vs baseline
        nrw_percentage = self._calculate_nrw(readings, day_anomalies)

        # Water loss estimate (m³/day)
        water_loss = self._calculate_water_loss(readings, day_anomalies)

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
                "max_pressure": round(max_pressure, 1),
                "min_pressure": round(min_pressure, 1),
                "max_flow": round(max_flow, 1),
                "min_flow": round(min_flow, 1),
                "nrw_percentage": round(nrw_percentage, 2),
                "water_loss_m3": round(water_loss, 2)
            },
            "anomalies": {
                "total": len(day_anomalies),
                "critical": len([a for a in day_anomalies if a.get("severity") == "CRITICAL"]),
                "high": len([a for a in day_anomalies if a.get("severity") == "HIGH"]),
                "medium": len([a for a in day_anomalies if a.get("severity") == "MEDIUM"]),
                "low": len([a for a in day_anomalies if a.get("severity") == "LOW"])
            },
            "incidents": {
                "total": len(day_incidents),
                "open": len([i for i in day_incidents if i.status.value not in ["CLOSED", "RESOLVED"]]),
                "resolved": len([i for i in day_incidents if i.status.value in ["RESOLVED", "CLOSED"]]),
                "critical_open": len([i for i in day_incidents if i.priority.value == "CRITICAL" and i.status.value not in ["CLOSED", "RESOLVED"]])
            },
            "readings": [{"timestamp": r.timestamp.isoformat(), "pressure_mca": r.pressure_mca, "flow_lps": r.flow_lps, "is_anomaly": r.quality_flag == "ANOMALY"} for r in readings],
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_weekly_report(self, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate weekly report with proper week bounds"""
        if end_date is None:
            end_date = self._now_peru()
        
        start_utc, end_utc = self._peru_week_bounds(end_date)

        # Get data for the week
        readings = self.telemetry_service.get_historical_readings(
            settings.target_dma,
            start_utc,
            end_utc,
            limit=10000
        )

        anomalies = self.anomaly_service.get_recent_anomalies(
            settings.target_dma,
            hours=168
        )
        # Filter to week bounds
        week_anomalies = [
            a for a in anomalies 
            if a.get("anomaly") and a["anomaly"].detected_at and 
            start_utc <= a["anomaly"].detected_at.replace(tzinfo=timezone.utc) < end_utc
        ]

        incidents = self.incident_service.get_all_tickets(
            dma_id=settings.target_dma
        )
        week_incidents = [
            i for i in incidents
            if i.created_at and start_utc <= i.created_at.replace(tzinfo=timezone.utc) < end_utc
        ]

        # Calculate daily averages
        daily_stats = []
        current = start_utc
        while current < end_utc:
            day_end = current + timedelta(days=1)
            day_readings = [r for r in readings if current <= r.timestamp.replace(tzinfo=timezone.utc) < day_end]
            
            if day_readings:
                daily_stats.append({
                    "date": current.strftime("%Y-%m-%d"),
                    "avg_pressure": round(sum(r.pressure_mca for r in day_readings) / len(day_readings), 1),
                    "avg_flow": round(sum(r.flow_lps for r in day_readings) / len(day_readings), 1),
                    "readings_count": len(day_readings),
                    "anomalies_count": len([a for a in week_anomalies if a.get("anomaly") and a["anomaly"].detected_at and current <= a["anomaly"].detected_at.replace(tzinfo=timezone.utc) < day_end]),
                    "water_loss": round(self._calculate_water_loss(day_readings, [a for a in week_anomalies if a.get("anomaly") and a["anomaly"].detected_at and current <= a["anomaly"].detected_at.replace(tzinfo=timezone.utc) < day_end]), 2)
                })
            
            current = day_end

        # Weekly totals
        total_readings = len(readings)
        total_anomalies = len(week_anomalies)
        total_incidents = len(week_incidents)
        total_water_loss = sum(d.get("water_loss", 0) for d in daily_stats)
        
        nrw_percentage = self._calculate_nrw(readings, week_anomalies)

        return {
            "period": {
                "start": start_utc.strftime("%Y-%m-%d"),
                "end": end_utc.strftime("%Y-%m-%d")
            },
            "dma": settings.target_dma,
            "daily_stats": daily_stats,
            "total_readings": total_readings,
            "total_anomalies": total_anomalies,
            "total_incidents": total_incidents,
            "water_loss_estimate": round(total_water_loss, 2),
            "nrw_percentage": round(nrw_percentage, 2),
            "anomaly_trend": self._calculate_trend(week_anomalies),
            "incident_trend": self._calculate_incident_trend(week_incidents),
            "generated_at": datetime.utcnow().isoformat()
        }

    def generate_custom_report(self, start_date: datetime, end_date: datetime, dma_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate custom report for a date range"""
        target_dma = dma_id or settings.target_dma
        
        # Ensure timezone awareness
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=PERU_TZ)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=PERU_TZ)
        
        start_utc = start_date.astimezone(timezone.utc)
        end_utc = end_date.astimezone(timezone.utc)

        readings = self.telemetry_service.get_historical_readings(target_dma, start_utc, end_utc, limit=10000)
        
        anomalies = self.anomaly_service.get_recent_anomalies(target_dma, hours=int((end_date - start_date).total_seconds() / 3600))
        period_anomalies = [a for a in anomalies if a.get("anomaly") and a["anomaly"].detected_at and start_utc <= a["anomaly"].detected_at.replace(tzinfo=timezone.utc) < end_utc]
        
        incidents = self.incident_service.get_all_tickets(dma_id=target_dma, limit=1000)
        period_incidents = [i for i in incidents if i.created_at and start_utc <= i.created_at.replace(tzinfo=timezone.utc) < end_utc]
        
        resolved_incidents = [i for i in period_incidents if i.status.value in ["RESOLVED", "CLOSED"]]
        
        nrw_percentage = self._calculate_nrw(readings, period_anomalies)
        water_loss = self._calculate_water_loss(readings, period_anomalies)

        return {
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            },
            "dma_id": target_dma,
            "statistics": {
                "total_readings": len(readings),
                "avg_pressure": round(sum(r.pressure_mca for r in readings) / len(readings), 1) if readings else 0,
                "avg_flow": round(sum(r.flow_lps for r in readings) / len(readings), 1) if readings else 0,
                "anomalies_detected": len(period_anomalies),
                "incidents_created": len(period_incidents),
                "incidents_resolved": len(resolved_incidents),
                "nrw_percentage": round(nrw_percentage, 2),
                "water_loss_m3": round(water_loss, 2)
            },
            "anomalies_list": [{
                "id": a.get("anomaly").id if a.get("anomaly") else a.get("id", "N/A"),
                "date": a.get("anomaly").detected_at.isoformat() if a.get("anomaly") and a.get("anomaly").detected_at else a.get("detected_at", ""),
                "severity": a.get("anomaly").severity.value if a.get("anomaly") and hasattr(a.get("anomaly").severity, "value") else a.get("severity", ""),
                "status": a.get("anomaly").status.value if a.get("anomaly") and hasattr(a.get("anomaly").status, "value") else a.get("status", "")
            } for a in period_anomalies],
            "incidents_list": [{
                "code": i.code,
                "title": i.title,
                "priority": i.priority.value if hasattr(i.priority, "value") else i.priority,
                "status": i.status.value if hasattr(i.status, "value") else i.status,
                "date": i.created_at.isoformat() if i.created_at else ""
            } for i in period_incidents],
            "generated_at": datetime.utcnow().isoformat()
        }

    def _calculate_nrw(self, readings: List, anomalies: List) -> float:
        """
        Calculate Non-Revenue Water percentage
        NRW = (System Input Volume - Billed Authorized Consumption) / System Input Volume * 100
        For MVP: Estimate based on anomaly flow excess vs baseline
        """
        if not readings:
            return 0.0
        
        # Baseline: normal flow without anomalies
        normal_readings = [r for r in readings if r.quality_flag != "ANOMALY"]
        if not normal_readings:
            return 0.0
        
        avg_normal_flow = sum(r.flow_lps for r in normal_readings) / len(normal_readings)
        
        # Calculate excess flow during anomalies (potential losses)
        total_excess = 0
        for a in anomalies:
            anomaly_obj = a.get("anomaly")
            if anomaly_obj and anomaly_obj.flow_variation and anomaly_obj.flow_variation > 0:
                total_excess += anomaly_obj.flow_variation * 3.6  # LPS to m³/h
        
        # System input volume (24h)
        system_input = avg_normal_flow * 86.4  # LPS * 86400s / 1000 = m³/day
        
        if system_input > 0:
            nrw = (total_excess / system_input) * 100
            return min(nrw, 50.0)  # Cap at 50% for sanity
        
        return 0.0

    def _calculate_water_loss(self, readings: List, anomalies: List) -> float:
        """Calculate estimated water loss in m³/day from anomalies"""
        if not readings:
            return 0.0
        
        total_loss = 0.0
        for a in anomalies:
            anomaly_obj = a.get("anomaly")
            if anomaly_obj and anomaly_obj.estimated_loss_volume:
                total_loss += anomaly_obj.estimated_loss_volume
            elif anomaly_obj and anomaly_obj.flow_variation and anomaly_obj.flow_variation > 0:
                # Estimate: flow excess * hours * 3.6
                hours = 1  # default 1 hour per anomaly
                total_loss += anomaly_obj.flow_variation * hours * 3.6
        
        return total_loss

    def _calculate_trend(self, anomalies: List[Dict]) -> Dict[str, Any]:
        """Calculate anomaly trend over time"""
        if not anomalies:
            return {"trend": "STABLE", "change_percentage": 0}
        
        daily_counts = {}
        for item in anomalies:
            anomaly = item.get("anomaly")
            if anomaly and anomaly.detected_at:
                date = anomaly.detected_at.strftime("%Y-%m-%d")
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

    def _calculate_incident_trend(self, incidents: List) -> Dict[str, Any]:
        """Calculate incident trend"""
        if not incidents:
            return {"trend": "STABLE", "change_percentage": 0}
        
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