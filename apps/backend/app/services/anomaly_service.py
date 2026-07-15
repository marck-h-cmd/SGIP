from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random

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

    def __init__(self, db_session=None, telemetry_service=None, incident_service=None):
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
        
        if isinstance(incident_service, DependsClass) or incident_service is None:
            from app.services.incident_service import IncidentService
            self.incident_service = IncidentService()
        else:
            self.incident_service = incident_service
        
        self.ml_model = IsolationForestModel()
        
        self._initialize_model()

    def _initialize_model(self):
        """Prepare ML model by training it if needed"""
        try:
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
                is_anomaly = reading.pressure_mca < 40.0 or reading.flow_lps > 35.0
                score = 0.8 if is_anomaly else 0.2
        else:
            is_anomaly = reading.pressure_mca < 40.0 or reading.flow_lps > 35.0
            score = 0.8 if is_anomaly else 0.2

        if reading.pressure_mca < 40.0 or reading.flow_lps > 35.0:
            is_anomaly = True
            if score < 0.8:
                score = 1.0

        anomaly_domain = None
        if is_anomaly:
            if reading.pressure_mca < 30.0 or reading.flow_lps > 45.0:
                severity = AnomalySeverity.CRITICAL
            elif reading.pressure_mca < 35.0 or reading.flow_lps > 40.0:
                severity = AnomalySeverity.HIGH
            elif reading.pressure_mca < 45.0 or reading.flow_lps > 35.0:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW

            pressure_var = reading.pressure_mca - 55.2
            flow_var = reading.flow_lps - 25.4
            loss_estimate = max(0.0, flow_var) * 3.6 if flow_var > 0 else 0.0

            anomaly_model = AnomalyModel(
                telemetry_id=1,
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
            
            self.alert_service.create_alert_from_anomaly(anomaly_domain)
            
            if severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
                try:
                    self.incident_service.create_incident(anomaly_domain)
                except Exception:
                    pass

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
        """
        Generar anomalías simuladas pero realistas usando escenarios del catálogo hidráulico.
        Cada anomalía tiene: tipo, descripción coherente, causa raíz, severidad, y efectos físicos.
        """
        from app.providers.mock_provider import MockTelemetryProvider
        from app.providers.anomaly_scenarios import get_random_scenario, select_severity, compute_effects
        
        dma_repo = DMARepository(self.db)
        if not dma_repo.get_by_code(dma_id):
            dma_repo.create(DMAModel(
                code=dma_id, name="Moche 01", district="Moche",
                status="ACTIVE", population=18000,
                description="Sector Moche - Zona urbana principal"
            ))

        now = datetime.utcnow()
        start = now - timedelta(hours=hours)
        
        # Generar entre 3 y 12 anomalías realistas según el período
        num_anomalies = min(max(3, hours // 6), 12)
        
        saved = []
        used_scenarios = set()
        
        for i in range(num_anomalies):
            # Seleccionar escenario (evitar repetir si es posible)
            scenario = get_random_scenario()
            attempts = 0
            while scenario.code in used_scenarios and attempts < 5:
                scenario = get_random_scenario()
                attempts += 1
            used_scenarios.add(scenario.code)
            
            # Seleccionar severidad
            severity = select_severity(scenario)
            
            # Calcular efectos físicos
            pressure_delta, flow_delta = compute_effects(scenario, severity)
            
            # Timestamp realista: distribuido a lo largo del período
            offset_hours = random.uniform(0.5, hours - 0.5)
            detected_at = now - timedelta(hours=offset_hours)
            
            # Baseline realista (55.2 MCA, 25.4 LPS)
            base_pressure = 55.2
            base_flow = 25.4
            final_pressure = base_pressure + pressure_delta
            final_flow = base_flow + flow_delta
            
            # Score de anomalía coherente con severidad
            score_map = {"CRITICAL": 0.92, "HIGH": 0.82, "MEDIUM": 0.68, "LOW": 0.45}
            base_score = score_map.get(severity, 0.6)
            anomaly_score = round(base_score + random.uniform(-0.05, 0.05), 3)
            
            # Pérdida estimada: solo si hay exceso de caudal
            estimated_loss = max(0.0, flow_delta * 3.6) if flow_delta > 0 else 0.0
            
            # Descripción completa con contexto
            description = (
                f"[{scenario.code}] {scenario.name}\n"
                f"Efecto: Presión {pressure_delta:+.1f} MCA (final: {final_pressure:.1f}), "
                f"Caudal {flow_delta:+.1f} LPS (final: {final_flow:.1f})\n"
                f"Causa probable: {scenario.root_cause}\n"
                f"Pérdida estimada: {estimated_loss:.1f} m³/h"
            )
            
            # Estado: la mayoría son PENDING, algunas CONFIRMED, muy pocas RESOLVED
            status_weights = {"PENDING": 0.5, "CONFIRMED": 0.3, "RESOLVED": 0.15, "REJECTED": 0.05}
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1
            )[0]
            
            model = AnomalyModel(
                telemetry_id=random.randint(1, 100),
                dma_id=dma_id,
                dma_name="Moche 01",
                anomaly_score=anomaly_score,
                severity=severity,
                status=status,
                detected_at=detected_at,
                pressure_variation=pressure_delta,
                flow_variation=flow_delta,
                estimated_loss_volume=round(estimated_loss, 2),
                description=description
            )
            
            # Ajustar fechas de confirmación/resolución según estado
            if status in ("CONFIRMED", "RESOLVED"):
                model.confirmed_at = detected_at + timedelta(hours=random.uniform(0.5, 4))
            if status == "RESOLVED":
                model.resolved_at = model.confirmed_at + timedelta(hours=random.uniform(2, 12)) if model.confirmed_at else detected_at + timedelta(hours=random.uniform(4, 24))
            
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
