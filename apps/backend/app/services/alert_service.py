from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.domain.anomaly import Anomaly, AnomalySeverity
from app.domain.incident import IncidentTicket


class AlertService:
    """Service for managing alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Dict[str, Any]] = []
        self._id_counter = 1
    
    def create_alert_from_anomaly(self, anomaly: Anomaly) -> Dict[str, Any]:
        """Create an alert from an anomaly"""
        severity_levels = {
            AnomalySeverity.CRITICAL: "CRITICAL",
            AnomalySeverity.HIGH: "HIGH",
            AnomalySeverity.MEDIUM: "MEDIUM",
            AnomalySeverity.LOW: "LOW"
        }
        
        alert = {
            "id": self._id_counter,
            "type": "ANOMALY",
            "severity": severity_levels.get(anomaly.severity, "MEDIUM"),
            "title": f"Anomalía detectada en {anomaly.dma_name}",
            "message": anomaly.description or f"Score de anomalía: {anomaly.anomaly_score:.3f}",
            "dma_id": anomaly.dma_id,
            "dma_name": anomaly.dma_name,
            "anomaly_id": anomaly.id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ACTIVE",
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved": False,
            "resolved_at": None
        }
        
        self.alerts.append(alert)
        self._id_counter += 1
        
        return alert
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [a for a in self.alerts if a["status"] == "ACTIVE" and not a["resolved"]]
    
    def get_alerts_by_dma(self, dma_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a specific DMA"""
        return [a for a in self.alerts if a["dma_id"] == dma_id]
    
    def acknowledge_alert(self, alert_id: int, user: str) -> Optional[Dict[str, Any]]:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_by"] = user
                alert["acknowledged_at"] = datetime.utcnow().isoformat()
                return alert
        return None
    
    def resolve_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["resolved"] = True
                alert["resolved_at"] = datetime.utcnow().isoformat()
                alert["status"] = "RESOLVED"
                return alert
        return None
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts"""
        active = self.get_active_alerts()
        critical = len([a for a in active if a["severity"] == "CRITICAL"])
        high = len([a for a in active if a["severity"] == "HIGH"])
        medium = len([a for a in active if a["severity"] == "MEDIUM"])
        low = len([a for a in active if a["severity"] == "LOW"])
        
        return {
            "total_active": len(active),
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "last_alert": active[0] if active else None
        }
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for a period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        return [a for a in self.alerts if a["timestamp"] >= cutoff_str]