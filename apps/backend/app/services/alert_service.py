from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import Depends

from app.domain.anomaly import Anomaly, AnomalySeverity
from app.domain.incident import IncidentTicket
from app.infrastructure.database import db
from app.infrastructure.repositories import AlertRepository
from app.infrastructure.models import AlertModel


class AlertService:
    """Service for managing alerts and notifications - uses database persistence"""

    def __init__(self, db_session=None):
        from fastapi.params import Depends as DependsClass
        if isinstance(db_session, DependsClass) or db_session is None:
            self.db = db.SessionLocal()
        else:
            self.db = db_session
        self.alert_repo = AlertRepository(self.db)

    def create_alert_from_anomaly(self, anomaly: Anomaly) -> Dict[str, Any]:
        """Create an alert from an anomaly and persist to database"""
        severity_levels = {
            AnomalySeverity.CRITICAL: "CRITICAL",
            AnomalySeverity.HIGH: "HIGH",
            AnomalySeverity.MEDIUM: "MEDIUM",
            AnomalySeverity.LOW: "LOW"
        }

        alert_model = AlertModel(
            type="ANOMALY",
            severity=severity_levels.get(anomaly.severity, "MEDIUM"),
            title=f"Anomalía detectada en {anomaly.dma_name}",
            message=anomaly.description or f"Score de anomalía: {anomaly.anomaly_score:.3f}",
            dma_id=anomaly.dma_id,
            dma_name=anomaly.dma_name,
            anomaly_id=anomaly.id,
            status="ACTIVE",
            acknowledged=False,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved=False,
            resolved_at=None,
        )

        saved = self.alert_repo.create(alert_model)
        return self._model_to_dict(saved)

    def get_active_alerts(self, dma_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active alerts, optionally filtered by DMA"""
        alerts = self.alert_repo.get_active(dma_id)
        return [self._model_to_dict(a) for a in alerts]

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Get all alerts (active and resolved)"""
        alerts = self.alert_repo.get_all()
        return [self._model_to_dict(a) for a in alerts]

    def get_alerts_by_dma(self, dma_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a specific DMA"""
        return self.get_active_alerts(dma_id)

    def acknowledge_alert(self, alert_id: int, user: str) -> Optional[Dict[str, Any]]:
        """Acknowledge an alert"""
        alert = self.alert_repo.get_by_id(alert_id)
        if alert:
            alert.acknowledged = True
            alert.acknowledged_by = user
            alert.acknowledged_at = datetime.utcnow()
            alert.status = "ACKNOWLEDGED"
            self.alert_repo.update(alert)
            return self._model_to_dict(alert)
        return None

    def resolve_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Resolve an alert"""
        alert = self.alert_repo.get_by_id(alert_id)
        if alert:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.status = "RESOLVED"
            self.alert_repo.update(alert)
            return self._model_to_dict(alert)
        return None

    def get_alert_summary(self, dma_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of alerts"""
        active = self.get_active_alerts(dma_id)
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

    def get_alert_history(self, hours: int = 24, dma_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alert history for a period"""
        alerts = self.alert_repo.get_history(hours, dma_id)
        return [self._model_to_dict(a) for a in alerts]

    def _model_to_dict(self, model: AlertModel) -> Dict[str, Any]:
        """Convert AlertModel to dictionary for API responses"""
        return {
            "id": model.id,
            "type": model.type,
            "severity": model.severity,
            "title": model.title,
            "message": model.message,
            "dma_id": model.dma_id,
            "dma_name": model.dma_name,
            "anomaly_id": model.anomaly_id,
            "incident_id": model.incident_id,
            "timestamp": model.created_at.isoformat() if model.created_at else None,
            "status": model.status,
            "acknowledged": model.acknowledged,
            "acknowledged_by": model.acknowledged_by,
            "acknowledged_at": model.acknowledged_at.isoformat() if model.acknowledged_at else None,
            "resolved": model.resolved,
            "resolved_at": model.resolved_at.isoformat() if model.resolved_at else None
        }