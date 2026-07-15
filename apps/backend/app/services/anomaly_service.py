from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.infrastructure.database import db
from app.infrastructure.repositories import AnomalyRepository, TelemetryRepository, DMARepository
from app.infrastructure.models import AnomalyModel, DMAModel
from app.domain.telemetry import TelemetryReading
from app.domain.anomaly import Anomaly, AnomalySeverity, AnomalyStatus
from app.ml.isolation_forest_model import IsolationForestModel
from app.services.alert_service import AlertService


class AnomalyService:
    """Service to handle anomaly detection logic"""

    def __init__(self, db_session=None, telemetry_service=None):
        from fastapi.params import Depends as DependsClass
        if isinstance(db_session, DependsClass) or db_session is None:
            self.db = db.SessionLocal()
        else:
            self.db = db_session
        self.anomaly_repo = AnomalyRepository(self.db)
        self.telemetry_repo = TelemetryRepository(self.db)
        
        if isinstance(telemetry_service, DependsClass) or telemetry_service is None:
            from app.services.telemetry_service import TelemetryService
            self.telemetry_service = TelemetryService()
        else:
            self.telemetry_service = telemetry_service
            
        self.alert_service = AlertService()
        self.ml_model = IsolationForestModel()
        
        self._initialize_model()

    def _initialize_model(self):
        """Prepare ML model by training it if needed"""
        try:
            # Generate dummy telemetry to train if database is empty
            # In a real app, we would query historical data
            readings = []
            now = datetime.utcnow()
            for i in range(120):
                readings.append(TelemetryReading(
                    timestamp=now - timedelta(hours=i),
                    dma_id=settings.target_dma,
                    dma_name=settings.target_dma_name,
                    sensor_id="SENS-MO-01-P",
                    pressure_mca=55.0 + 2.0 * (i % 24 == 12) + (i % 5) * 0.2,
                    flow_lps=25.0 - 1.0 * (i % 24 == 12) + (i % 3) * 0.1,
                    source="mock",
                    quality_flag="GOOD"
                ))
            self.ml_model.train(readings)
        except Exception as e:
            print(f"Error training initial model: {e}")

    def analyze_reading(self, reading: TelemetryReading) -> Dict[str, Any]:
        """Analyze a telemetry reading and record anomaly if detected"""
        is_anomaly = False
        score = 0.1
        analysis = {}

        if self.ml_model.is_trained:
            try:
                is_anomaly, score, analysis = self.ml_model.predict(reading)
            except Exception as e:
                # Heuristic fallback if model prediction fails
                is_anomaly = reading.pressure_mca < 40.0 or reading.flow_lps > 35.0
                score = 0.8 if is_anomaly else 0.2
        else:
            is_anomaly = reading.pressure_mca < 40.0 or reading.flow_lps > 35.0
            score = 0.8 if is_anomaly else 0.2

        # Override ML model for extreme threshold breaches
        # (Isolation Forest may fail to score points far outside its training bounding box)
        if reading.pressure_mca < 40.0 or reading.flow_lps > 35.0:
            is_anomaly = True
            if score < 0.8:
                score = 1.0  # Force a high score for extreme breaches

        anomaly_domain = None
        if is_anomaly:
            # Severity based on physical thresholds (ordered from most to least severe)
            if reading.pressure_mca < 30.0 or reading.flow_lps > 45.0:
                severity = AnomalySeverity.CRITICAL
            elif reading.pressure_mca < 35.0 or reading.flow_lps > 40.0:
                severity = AnomalySeverity.HIGH
            elif reading.pressure_mca < 45.0 or reading.flow_lps > 35.0:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW

            # Calculate variations vs. normal baseline
            pressure_var = reading.pressure_mca - 55.2
            flow_var = reading.flow_lps - 25.4
            
            # Loss estimation: excess flow * 3600 sec (liters per hour) / 1000 → m³
            loss_estimate = max(0.0, flow_var) * 3.6 if flow_var > 0 else 0.0

            # Save model to database
            anomaly_model = AnomalyModel(
                telemetry_id=1,  # mock or real reference
                dma_id=reading.dma_id,
                dma_name=reading.dma_name,
                anomaly_score=score,
                severity=severity.value,
                status=AnomalyStatus.PENDING.value,
                pressure_variation=pressure_var,
                flow_variation=flow_var,
                estimated_loss_volume=loss_estimate,
                description=f"Variación hidráulica: Presión ({pressure_var:.1f} MCA), Caudal ({flow_var:.1f} LPS)"
            )
            saved = self.anomaly_repo.create(anomaly_model)
            
            anomaly_domain = Anomaly(
                id=saved.id,
                telemetry_id=saved.telemetry_id,
                dma_id=saved.dma_id,
                dma_name=saved.dma_name,
                anomaly_score=saved.anomaly_score,
                severity=AnomalySeverity(saved.severity),
                status=AnomalyStatus(saved.status),
                detected_at=saved.detected_at,
                pressure_variation=saved.pressure_variation,
                flow_variation=saved.flow_variation,
                estimated_loss_volume=saved.estimated_loss_volume,
                description=saved.description
            )
            
            # Trigger alert
            self.alert_service.create_alert_from_anomaly(anomaly_domain)

        return {
            "is_anomaly": is_anomaly,
            "score": score,
            "anomaly": anomaly_domain,
            "analysis": analysis
        }

    def analyze_dma(self, dma_id: str, hours: int = 24) -> Dict[str, Any]:
        """Analyze a whole DMA history for anomalies"""
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        # Usar el servicio de telemetría (que usa el proveedor mock con caché)
        readings = self.telemetry_service.get_historical_readings(dma_id, start, end)
        
        anomalies_found = []
        for r in readings:
            reading_domain = TelemetryReading(
                timestamp=r.timestamp,
                dma_id=r.dma_id,
                dma_name=r.dma_name,
                sensor_id=r.sensor_id,
                pressure_mca=r.pressure_mca,
                flow_lps=r.flow_lps,
                source=r.source,
                quality_flag=r.quality_flag
            )
            res = self.analyze_reading(reading_domain)
            if res["is_anomaly"]:
                anomalies_found.append(res["anomaly"])

        return {
            "dma_id": dma_id,
            "hours_analyzed": hours,
            "readings_checked": len(readings),
            "anomalies_count": len(anomalies_found),
            "anomalies": anomalies_found
        }

    def get_recent_anomalies(self, dma_id: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent anomalies formatted for routes"""
        db_anomalies = self.anomaly_repo.get_recent(dma_id, hours)
        if not db_anomalies:
            db_anomalies = self._generate_mock_anomalies(dma_id or settings.target_dma, hours)
        results = []
        for a in db_anomalies:
            anomaly_domain = Anomaly(
                id=a.id,
                telemetry_id=a.telemetry_id,
                dma_id=a.dma_id,
                dma_name=a.dma_name,
                anomaly_score=a.anomaly_score,
                severity=AnomalySeverity(a.severity),
                status=AnomalyStatus(a.status),
                detected_at=a.detected_at,
                pressure_variation=a.pressure_variation,
                flow_variation=a.flow_variation,
                estimated_loss_volume=a.estimated_loss_volume,
                description=a.description
            )
            results.append({
                "anomaly": anomaly_domain,
                "score": a.anomaly_score,
                "severity": a.severity,
                "is_anomaly": True
            })
        return results

    def _generate_mock_anomalies(self, dma_id: str, hours: int) -> list:
        from app.providers.mock_provider import MockTelemetryProvider
        dma_repo = DMARepository(self.db)
        if not dma_repo.get_by_code(dma_id):
            dma_repo.create(DMAModel(code=dma_id, name=dma_id, district="Moche", status="ACTIVE", population=18000))
        provider = MockTelemetryProvider()
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        readings = provider.get_historical_readings(dma_id, start, end, limit=96)
        saved = []
        for r in readings:
            is_anomaly = r.pressure_mca < 40.0 or r.flow_lps > 35.0
            if not is_anomaly:
                continue
            severity = "CRITICAL" if r.pressure_mca < 30.0 or r.flow_lps > 45.0 else \
                       "HIGH" if r.pressure_mca < 35.0 or r.flow_lps > 40.0 else \
                       "MEDIUM" if r.pressure_mca < 45.0 else "LOW"
            pressure_var = r.pressure_mca - 55.2
            flow_var = r.flow_lps - 25.4
            model = AnomalyModel(
                telemetry_id=1, dma_id=r.dma_id, dma_name=r.dma_name,
                anomaly_score=0.85, severity=severity, status="PENDING",
                pressure_variation=pressure_var, flow_variation=flow_var,
                estimated_loss_volume=max(0.0, flow_var) * 3.6,
                description=f"Variación hidráulica: Presión ({pressure_var:.1f} MCA), Caudal ({flow_var:.1f} LPS)"
            )
            saved.append(self.anomaly_repo.create(model))
        return saved

    def _calculate_severity_distribution(self, anomalies: List[Dict[str, Any]]) -> Dict[str, int]:
        """Helper to calculate severity distribution"""
        dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for a in anomalies:
            anomaly = a.get("anomaly")
            if anomaly:
                sev_val = anomaly.severity.value if hasattr(anomaly.severity, "value") else str(anomaly.severity)
                if sev_val in dist:
                    dist[sev_val] += 1
        return dist
