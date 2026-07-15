from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import random

from app.core.config import settings
from app.infrastructure.database import db
from app.infrastructure.repositories import IncidentRepository, AnomalyRepository, DMARepository, IncidentAuditLogRepository
from app.infrastructure.models import IncidentTicketModel, DMAModel, AnomalyModel, IncidentAuditLogModel
from app.domain.incident import IncidentTicket, IncidentPriority, IncidentStatus
from app.domain.anomaly import Anomaly, AnomalySeverity
from app.core.exceptions import NotFoundException, ValidationException

# Zona horaria de Perú (UTC-5)
PERU_TZ = timezone(timedelta(hours=-5))


class IncidentService:
    """Service to manage ITIL incident tickets and SLA compliance"""

    def __init__(self, db_session=None):
        from fastapi.params import Depends as DependsClass
        if isinstance(db_session, DependsClass) or db_session is None:
            self.db = db.SessionLocal()
        else:
            self.db = db_session
        self.incident_repo = IncidentRepository(self.db)
        self.anomaly_repo = AnomalyRepository(self.db)
        self.audit_repo = IncidentAuditLogRepository(self.db)

    def _now_peru(self) -> datetime:
        """Get current time in Peru timezone"""
        return datetime.now(PERU_TZ)

    def _utc_to_peru(self, dt: datetime) -> datetime:
        """Convert UTC datetime to Peru timezone"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(PERU_TZ)

    def _peru_to_utc(self, dt: datetime) -> datetime:
        """Convert Peru timezone datetime to UTC"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=PERU_TZ)
        return dt.astimezone(timezone.utc)

    def _calculate_sla_due(self, priority: IncidentPriority, created_at: datetime) -> datetime:
        """Calculate SLA due date based on priority and creation time (in Peru TZ)"""
        sla_hours = {
            IncidentPriority.CRITICAL: 2,
            IncidentPriority.HIGH: 4,
            IncidentPriority.MEDIUM: 8,
            IncidentPriority.LOW: 24
        }
        hours = sla_hours.get(priority, 8)
        # created_at is already in UTC, convert to Peru for SLA calc
        local_created = self._utc_to_peru(created_at)
        due_local = local_created + timedelta(hours=hours)
        return self._peru_to_utc(due_local)

    def _log_audit(
        self,
        ticket_id: int,
        user: str,
        action: str,
        from_status: Optional[str] = None,
        to_status: Optional[str] = None,
        from_value: Optional[str] = None,
        to_value: Optional[str] = None,
        comment: Optional[str] = None
    ):
        """Log audit trail for ticket changes"""
        audit_log = IncidentAuditLogModel(
            ticket_id=ticket_id,
            user=user,
            action=action,
            from_status=from_status,
            to_status=to_status,
            from_value=from_value,
            to_value=to_value,
            comment=comment,
            created_at=self._peru_to_utc(self._now_peru())
        )
        self.audit_repo.create(audit_log)

    def create_incident(self, anomaly: Anomaly) -> IncidentTicket:
        """Create a new incident ticket from a detected anomaly with realistic data"""
        # Generate code: INC-YYYYMMDD-XXX
        today_str = datetime.now(PERU_TZ).strftime("%Y%m%d")
        existing_today = self.incident_repo.get_all(dma_id=anomaly.dma_id)
        sequence = len(existing_today) + 1
        code = f"INC-{today_str}-{sequence:03d}"

        # Determine priority from anomaly severity
        priority_map = {
            AnomalySeverity.CRITICAL: IncidentPriority.CRITICAL,
            AnomalySeverity.HIGH: IncidentPriority.HIGH,
            AnomalySeverity.MEDIUM: IncidentPriority.MEDIUM,
            AnomalySeverity.LOW: IncidentPriority.LOW
        }
        priority = priority_map.get(anomaly.severity, IncidentPriority.MEDIUM)

        # SLA calculation
        sla_hours = {
            IncidentPriority.CRITICAL: 2,
            IncidentPriority.HIGH: 4,
            IncidentPriority.MEDIUM: 8,
            IncidentPriority.LOW: 24
        }
        sla_duration = sla_hours.get(priority, 8)
        sla_due_at = datetime.now(PERU_TZ) + timedelta(hours=sla_duration)

        default_operator = "c.mendoza@sedalib.pe"

        # Extract anomaly code for better title
        anomaly_code = "FUGA_SUB"
        if anomaly.description and "[" in anomaly.description and "]" in anomaly.description:
            try:
                anomaly_code = anomaly.description.split("[")[1].split("]")[0]
            except:
                pass

        # Map anomaly codes to descriptive titles
        title_map = {
            "FUGA_SUB": "Fuga subterránea detectada",
            "FUGA_SUP": "Fuga superficial visible",
            "FUGA_ENT": "Fuga en entrada de predio",
            "ROTURA_TUB": "Rotura de tubería principal",
            "ROTURA_AC": "Rotura de acoplamiento",
            "ROBO_AGA": "Posible conexión clandestina",
            "SOBREPRES": "Sobrepresión en red",
            "BOMBA_OFF": "Parada de bomba detectada",
            "VALVULA_C": "Válvula de corte parcial",
            "SENSOR_ERR": "Falla de sensor detectada",
            "AIRE_RED": "Aire en red detectado",
            "CONSUMO_IND": "Consumo industrial anómalo"
        }

        title = f"{title_map.get(anomaly_code, 'Incidencia hidráulica')} en {anomaly.dma_name}"

        ticket_model = IncidentTicketModel(
            code=code,
            anomaly_id=anomaly.id,
            dma_id=anomaly.dma_id,
            dma_name=anomaly.dma_name,
            title=title,
            description=anomaly.description or "Detección de anomalía en lecturas de presión y caudal",
            priority=priority.value,
            status=IncidentStatus.NEW.value,
            assigned_to=default_operator,
            sla_due_at=sla_due_at
        )

        saved = self.incident_repo.create(ticket_model)
        return self._to_domain(saved)

    def create_incident_from_anomaly(
        self,
        anomaly_id: int,
        user: str = "operator"
    ) -> IncidentTicket:
        """Create an incident directly from an anomaly ID"""
        anomalies = self.anomaly_repo.get_recent(dma_id=None, hours=168)
        anomaly = None
        for a in anomalies:
            if a.id == anomaly_id:
                anomaly = a
                break
        
        if not anomaly:
            raise NotFoundException("Anomaly", str(anomaly_id))
        
        # Convert to domain anomaly
        anomaly_domain = Anomaly(
            id=anomaly.id,
            telemetry_id=anomaly.telemetry_id,
            dma_id=anomaly.dma_id,
            dma_name=anomaly.dma_name,
            anomaly_score=anomaly.anomaly_score,
            severity=AnomalySeverity(anomaly.severity),
            status=AnomalyStatus(anomaly.status),
            detected_at=anomaly.detected_at,
            pressure_variation=anomaly.pressure_variation,
            flow_variation=anomaly.flow_variation,
            estimated_loss_volume=anomaly.estimated_loss_volume,
            description=anomaly.description
        )
        
        ticket = self.create_incident(anomaly_domain)
        self._log_audit(ticket.id, user, "CREATED", comment="Incidente creado desde anomalía")
        return ticket

    def get_all_tickets(
        self,
        status: Optional[IncidentStatus] = None,
        dma_id: Optional[str] = None,
        priority: Optional[IncidentPriority] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[IncidentTicket]:
        """Get tickets with filters"""
        status_val = status.value if status else None
        priority_val = priority.value if priority else None
        
        tickets = self.incident_repo.get_all(status_val, dma_id, priority_val, limit, offset)
        if not tickets:
            tickets = self._generate_mock_incidents(dma_id or settings.target_dma, limit)
        return [self._to_domain(t) for t in tickets]

    def get_ticket(self, ticket_id: int) -> Optional[IncidentTicket]:
        """Get ticket by ID"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            return None
        return self._to_domain(ticket)

    def get_ticket_by_code(self, code: str) -> Optional[IncidentTicket]:
        """Get ticket by Code"""
        ticket = self.incident_repo.get_by_code(code)
        if not ticket:
            return None
        return self._to_domain(ticket)

    def update_ticket_status(
        self,
        ticket_id: int,
        status: IncidentStatus,
        user: str = "operator",
        notes: Optional[str] = None
    ) -> IncidentTicket:
        """Update incident status validating ITIL state transition rules"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket", str(ticket_id))

        current_status = IncidentStatus(ticket.status)
        
        # ITIL transitions validation
        valid_transitions = {
            IncidentStatus.NEW: [IncidentStatus.CLASSIFIED, IncidentStatus.REJECTED],
            IncidentStatus.CLASSIFIED: [IncidentStatus.ASSIGNED, IncidentStatus.REJECTED],
            IncidentStatus.ASSIGNED: [IncidentStatus.IN_PROGRESS, IncidentStatus.CANCELLED],
            IncidentStatus.IN_PROGRESS: [IncidentStatus.RESOLVED, IncidentStatus.CANCELLED, IncidentStatus.ESCALATED],
            IncidentStatus.ESCALATED: [IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED],
            IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.REOPENED, IncidentStatus.IN_PROGRESS],
            IncidentStatus.CLOSED: [IncidentStatus.REOPENED],
            IncidentStatus.REOPENED: [IncidentStatus.IN_PROGRESS, IncidentStatus.RESOLVED, IncidentStatus.CANCELLED],
            IncidentStatus.REJECTED: [IncidentStatus.CLOSED],
            IncidentStatus.CANCELLED: [IncidentStatus.CLOSED],
        }

        if status not in valid_transitions.get(current_status, []):
            raise ValidationException(f"Transición de estado inválida de {current_status.value} a {status.value}")

        from_status = current_status.value
        
        now = self._now_peru()
        now_utc = self._peru_to_utc(now)
        
        ticket.status = status.value
        ticket.updated_at = now_utc

        comment = notes or f"Cambio de estado: {from_status} → {status.value}"

        if status == IncidentStatus.RESOLVED:
            ticket.resolved_at = now_utc
            diff = now_utc - ticket.created_at
            ticket.resolution_time_minutes = int(diff.total_seconds() / 60)
            
            # Update associated anomaly
            anomaly = self.anomaly_repo.get_by_id(ticket.anomaly_id)
            if anomaly:
                anomaly.status = "RESOLVED"
                anomaly.resolved_at = now_utc
                self.anomaly_repo.update(anomaly)
                
        elif status == IncidentStatus.CLOSED:
            ticket.closed_at = now_utc
            
        elif status == IncidentStatus.ASSIGNED:
            # Response time calculation
            diff = now_utc - ticket.created_at
            ticket.response_time_minutes = int(diff.total_seconds() / 60)
            
        elif status == IncidentStatus.ESCALATED:
            # Escalation: notify management, reduce SLA by half remaining time
            comment = f"ESCALADO: {comment or 'SLA breach imminent'}"
            # Could create an SLA_BREACH alert here

        updated = self.incident_repo.update(ticket)
        
        # Audit log
        self._log_audit(
            ticket_id=ticket_id,
            user=user,
            action="STATUS_CHANGE",
            from_status=from_status,
            to_status=status.value,
            comment=comment
        )

        return self._to_domain(updated)

    def assign_ticket(self, ticket_id: int, assigned_to: str, user: str = "operator") -> IncidentTicket:
        """Assign incident ticket to operator"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket", str(ticket_id))

        ticket.status = IncidentStatus.ASSIGNED.value
        ticket.assigned_to = assigned_to
        ticket.updated_at = self._peru_to_utc(self._now_peru())
        
        diff = ticket.updated_at - ticket.created_at
        ticket.response_time_minutes = int(diff.total_seconds() / 60)

        updated = self.incident_repo.update(ticket)
        
        # Audit log
        self._log_audit(
            ticket_id=ticket_id,
            user=user,
            action="ASSIGNED",
            from_status=ticket.status,
            to_status=IncidentStatus.ASSIGNED.value,
            comment=f"Asignado a {assigned_to}"
        )

        return self._to_domain(updated)

    def _generate_mock_incidents(self, dma_id: str, limit: int = 10) -> list:
        """
        Generar incidencias realistas basadas en las anomalías del catálogo hidráulico.
        Cada incidencia tiene: título descriptivo, descripción detallada, prioridad coherente, y estados realistas.
        """
        dma_repo = DMARepository(self.db)
        if not dma_repo.get_by_code(dma_id):
            dma_repo.create(DMAModel(
                code=dma_id, name="Moche 01", district="Moche",
                status="ACTIVE", population=18000,
                description="Sector Moche - Zona urbana principal"
            ))
            
        # Obtener anomalías reales de la BD (últimos 7 días)
        anomalies = self.anomaly_repo.get_recent(dma_id, hours=168)
        
        if not anomalies:
            return []

        now = self._peru_to_utc(self._now_peru())
        saved = []
        
        # Mapeo de códigos de anomalía a títulos y descripciones de incidencias
        incident_templates = {
            "FUGA_SUB": {
                "titles": [
                    "Fuga subterránea detectada en sector {sector}",
                    "Pérdida subterránea confirmada - {sector}",
                    "Alerta de fuga clandestina en {sector}"
                ],
                "descriptions": [
                    "Se ha detectado una fuga subterránea en el sector {sector}. El análisis de variación hidráulica muestra una caída de presión de {pressure} MCA y un incremento de caudal de {flow} LPS. Se requiere inspección con correlador acústico para localizar el punto exacto de la fuga.",
                    "Variación anormal en la red indica fuga subterránea. Presión reducida: {pressure} MCA, Caudal incrementado: {flow} LPS. Posible rotura de tubería de asbesto-cemento. Coordinar equipo de campo para verificación."
                ],
                "actions": ["Inspección acústica programada", "Equipo de campo despachado", "Análisis de zona en progreso"]
            },
            "FUGA_SUP": {
                "titles": [
                    "Fuga superficial visible en {sector}",
                    "Fuga en vía pública reportada - {sector}",
                    "Pérdida de agua superficial detectada - {sector}"
                ],
                "descriptions": [
                    "Se ha identificado una fuga superficial en el sector {sector}. Se observa humedad y acumulación de agua en la superficie. Caudal incrementado en {flow} LPS con reducción de presión de {pressure} MCA. Requiere intervención inmediata.",
                    "Reporte de fuga visible en {sector}. El water audit indica pérdida activa. Presión: {pressure} MCA, Caudal: {flow} LPS. Coordinar acometida de emergencia."
                ],
                "actions": ["Acometida de emergencia coordinada", "Señalización de área", "Corte parcial programado"]
            },
            "FUGA_ENT": {
                "titles": [
                    "Fuga en entrada de predio - {sector}",
                    "Conexión defectuosa detectada - {sector}",
                    "Pérdida en acometida predial - {sector}"
                ],
                "descriptions": [
                    "Se detecta fuga en conexión de entrada a predio en {sector}. Caudal elevado durante horario nocturno. Variación: Presión {pressure} MCA, Caudal {flow} LPS. Posible conexión clandestina o deterioro de llave de paso.",
                    "Anomalía en acometida predial del sector {sector}. Consumo nocturno anormal sugiere fuga o conexión no autorizada. Presión: {pressure} MCA, Caudal: {flow} LPS."
                ],
                "actions": ["Visita técnica programada", "Revisión de contrato pendiente", "Medición nocturna realizada"]
            },
            "ROTURA_TUB": {
                "titles": [
                    "Rotura de tubería principal en {sector}",
                    "Emergencia: Rotura de red en {sector}",
                    "Acometida de emergencia requerida - {sector}"
                ],
                "descriptions": [
                    "ROTURA DE TUBERÍA PRINCIPAL en {sector}. Caída súbita de presión de {pressure} MCA y aumento extremo de caudal de {flow} LPS. Se requiere acometida de emergencia inmediata para isolation del tramo afectado.",
                    "Emergencia hidráulica en {sector}: Rotura de tubería de distribución. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Activar protocolo de emergencia y notificar a usuarios afectados."
                ],
                "actions": ["Protocolo de emergencia activado", "Aislamiento de tramo", "Notificación a usuarios", "Equipo de reparación despachado"]
            },
            "ROTURA_AC": {
                "titles": [
                    "Rotura de acoplamiento en {sector}",
                    "Desconexión de unión detectada - {sector}",
                    "Fuga en acoplamiento de tubería - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado rotura de acoplamiento en {sector}. Pérdida moderada con variabilidad según presión de red. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Requiere reacoplamiento.",
                    "Desconexión parcial de acoplamiento en {sector}. La unión muestra desgaste. Variación: Presión {pressure} MCA, Caudal {flow} LPS."
                ],
                "actions": ["Reacoplamiento programado", "Inspección visual realizada", "Materiales solicitados"]
            },
            "ROBO_AGA": {
                "titles": [
                    "Posible conexión clandestina - {sector}",
                    "Alerta de robo de agua en {sector}",
                    "Consumo irregular detectado - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado incremento sostenido de caudal sin variación significativa de presión en {sector}. Patrón sugiere conexión no autorizada al tendido. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Se requiere auditoría de conexiones.",
                    "Anomalía compatible con robo de agua en {sector}. Caudal elevado ({flow} LPS) con presión estable ({pressure} MCA). Programar inspección de campo y revisión de contratos."
                ],
                "actions": ["Auditoría de conexiones programada", "Revisión de contratos", "Inspección nocturna realizada"]
            },
            "SOBREPRES": {
                "titles": [
                    "Sobrepresión en red detectada - {sector}",
                    "Alerta de alta presión - {sector}",
                    "Exceso de presión en sistema - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado sobrepresión en el sector {sector}. Presión anormalmente alta que puede dañar conexiones y artefactos. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Revisar variador de bomba o válvula reguladora.",
                    "Sobrepresión en red de {sector}. Riesgo de roturas secundarias por exceso de presión. Presión: {pressure} MCA, Caudal: {flow} LPS. Ajustar regulación de bomba."
                ],
                "actions": ["Revisión de bomba programada", "Ajuste de variador", "Monitoreo intensivo"]
            },
            "BOMBA_OFF": {
                "titles": [
                    "Parada de bomba detectada - {sector}",
                    "Falla de estación de bombeo - {sector}",
                    "Corte de energía en bombeo - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado parada de estación de bombeo en {sector}. Caída brusca de presión y caudal. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Verificar suministro eléctrico y estado de bomba.",
                    "Falla en sistema de bombeo del sector {sector}. Presión reducida: {pressure} MCA, Caudal: {flow} LPS. Activar respaldo si está disponible."
                ],
                "actions": ["Verificación eléctrica", "Bomba de respaldo activada", "Notificación a subestación"]
            },
            "VALVULA_C": {
                "titles": [
                    "Válvula de corte parcial detectada - {sector}",
                    "Obstrucción en válvula de seccionamiento - {sector}",
                    "Válvula atascada en {sector}"
                ],
                "descriptions": [
                    "Se ha detectado válvula de seccionamiento parcialmente cerrada en {sector}. Reduce caudal y presión aguas abajo. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Requiere operación de válvula.",
                    "Válvula obstruida por sedimentos en {sector}. Flujo restringido. Presión: {pressure} MCA, Caudal: {flow} LPS. Programar limpieza o reemplazo."
                ],
                "actions": ["Operación de válvula programada", "Limpieza de sedimentos", "Monitoreo de presión"]
            },
            "SENSOR_ERR": {
                "titles": [
                    "Falla de sensor detectada - {sector}",
                    "Errata de medición en {sector}",
                    "Calidad de datos comprometida - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado lecturas erráticas del sensor en {sector}. Patrón no consistente con comportamiento hidráulico real. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Verificar transmisor y cables.",
                    "Falla en sistema de medición del sector {sector}. Lecturas fuera de rango físico. Presión: {pressure} MCA, Caudal: {flow} LPS. Calibración requerida."
                ],
                "actions": ["Calibración de sensor", "Revisión de cables", "Validación de datos"]
            },
            "AIRE_RED": {
                "titles": [
                    "Aire en red detectado - {sector}",
                    "Fluctuaciones por aire en tubería - {sector}",
                    "Presencia de aire en sistema - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado presencia de aire en la red del sector {sector}. Causa fluctuaciones erráticas de presión. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Revisar juntas y válvulas aireadoras.",
                    "Aire entrañado en tuberías del sector {sector}. Lecturas inestables. Presión: {pressure} MCA, Caudal: {flow} LPS. Verificar tanque de nivel y válvulas."
                ],
                "actions": ["Purga de aire programada", "Revisión de juntas", "Verificación de tanque"]
            },
            "CONSUMO_IND": {
                "titles": [
                    "Consumo industrial anómalo detectado - {sector}",
                    "Exceso de dotación contratada - {sector}",
                    "Usuario con consumo fuera de contrato - {sector}"
                ],
                "descriptions": [
                    "Se ha detectado incremento sostenido de caudal por usuario industrial en {sector}. Consumo excede dotación contratada. Efecto: Presión {pressure} MCA, Caudal {flow} LPS. Revisar contrato y medición.",
                    "Anomalía de consumo en sector {sector}. Usuario industrial con consumo no autorizado. Presión: {pressure} MCA, Caudal: {flow} LPS. Notificar a comercial."
                ],
                "actions": ["Revisión de contrato", "Medición en predio", "Notificación a commercial"]
            }
        }
        
        for i, anomaly in enumerate(anomalies[:limit]):
            severity = anomaly.severity
            priority_map = {
                "CRITICAL": IncidentPriority.CRITICAL,
                "HIGH": IncidentPriority.HIGH,
                "MEDIUM": IncidentPriority.MEDIUM,
                "LOW": IncidentPriority.LOW
            }
            priority = priority_map.get(severity, IncidentPriority.MEDIUM)
            
            # Extraer código de anomalía de la descripción si existe
            anomaly_code = "FUGA_SUB"  # Default
            if anomaly.description and "[" in anomaly.description and "]" in anomaly.description:
                try:
                    anomaly_code = anomaly.description.split("[")[1].split("]")[0]
                except:
                    pass
            
            # Obtener template de incidencia
            template = incident_templates.get(anomaly_code, incident_templates["FUGA_SUB"])
            
            # Seleccionar título y descripción aleatorios
            title_template = random.choice(template["titles"])
            desc_template = random.choice(template["descriptions"])
            
            # Valores para formateo
            pressure_val = abs(anomaly.pressure_variation) if anomaly.pressure_variation else 0
            flow_val = anomaly.flow_variation if anomaly.flow_variation else 0
            
            title = title_template.format(sector="Moche 01")
            description = desc_template.format(
                sector="Moche 01",
                pressure=f"{pressure_val:+.1f}" if anomaly.pressure_variation else "N/A",
                flow=f"{flow_val:+.1f}" if anomaly.flow_variation else "N/A"
            )
            
            # Estado de la incidencia: más realista
            # Las incidencias críticas tienden a resolverse más rápido
            status_weights = {
                "NEW": 0.15,
                "CLASSIFIED": 0.1,
                "ASSIGNED": 0.15,
                "IN_PROGRESS": 0.25,
                "RESOLVED": 0.25,
                "CLOSED": 0.1
            }
            # Ajustar pesos según prioridad
            if severity == "CRITICAL":
                status_weights["RESOLVED"] = 0.35
                status_weights["NEW"] = 0.05
            elif severity == "LOW":
                status_weights["NEW"] = 0.25
                status_weights["RESOLVED"] = 0.15
            
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1
            )[0]
            
            # Tiempo de creación coherente con la anomalía
            created_raw = anomaly.detected_at if anomaly.detected_at else now - timedelta(hours=i * 4)
            if created_raw.tzinfo is None:
                created = self._peru_to_utc(created_raw.replace(tzinfo=PERU_TZ))
            else:
                created = created_raw
            
            sla_due = self._calculate_sla_due(priority, created)
            
            # Tiempo de resolución realista según severidad
            resolved = None
            resolution_hours = {
                "CRITICAL": (1, 4),
                "HIGH": (2, 8),
                "MEDIUM": (4, 24),
                "LOW": (8, 48)
            }
            min_h, max_h = resolution_hours.get(severity, (4, 24))
            
            if status in ("RESOLVED", "CLOSED"):
                resolved = created + timedelta(hours=random.randint(min_h, max_h))
            
            # Asignación realista
            assigned_to = None
            if status in ("ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"):
                operators = [
                    "j.garcia@sedalib.pe",
                    "m.rodriguez@sedalib.pe",
                    "c.mendoza@sedalib.pe",
                    "l.torres@sedalib.pe",
                    "equipo.campo@sedalib.pe"
                ]
                assigned_to = random.choice(operators)
            
            # Tiempo de respuesta y resolución
            response_time = None
            resolution_time = None
            
            if status not in ("NEW",):
                response_time = random.randint(5, 120)
            
            if resolved:
                resolution_time = int((resolved - created).total_seconds() / 60)
            
            model = IncidentTicketModel(
                code=f"INC-{created.strftime('%Y%m%d')}-{i+1:03d}",
                anomaly_id=anomaly.id,
                dma_id=dma_id,
                dma_name=anomaly.dma_name,
                title=title,
                description=description,
                priority=priority.value,
                status=status,
                assigned_to=assigned_to,
                created_at=created,
                updated_at=now,
                sla_due_at=sla_due,
                resolved_at=resolved,
                response_time_minutes=response_time,
                resolution_time_minutes=resolution_time
            )
            saved.append(self.incident_repo.create(model))
        
        return saved

    def get_sla_metrics(self) -> Dict[str, Any]:
        """Calculate SLA compliance metrics"""
        tickets = self.incident_repo.get_all(limit=1000)
        total = len(tickets)
        if total == 0:
            return {
                "total_tickets": 0,
                "sla_compliance_rate": 100.0,
                "breached_tickets": 0,
                "critical_tickets": 0,
                "open_tickets": 0
            }

        breached = 0
        critical = 0
        open_count = 0
        now = self._peru_to_utc(self._now_peru())

        for t in tickets:
            is_open = t.status not in [IncidentStatus.CLOSED.value, IncidentStatus.RESOLVED.value, 
                                       IncidentStatus.REJECTED.value, IncidentStatus.CANCELLED.value]
            if is_open:
                open_count += 1
                sla_due = t.sla_due_at
                if sla_due is not None and sla_due.tzinfo is None:
                    sla_due = sla_due.replace(tzinfo=timezone.utc)
                if sla_due is not None and now > sla_due:
                    breached += 1
            else:
                resolution_time = t.resolved_at or t.closed_at
                if resolution_time is not None and resolution_time.tzinfo is None:
                    resolution_time = resolution_time.replace(tzinfo=timezone.utc)
                sla_due = t.sla_due_at
                if sla_due is not None and sla_due.tzinfo is None:
                    sla_due = sla_due.replace(tzinfo=timezone.utc)
                if resolution_time and sla_due and resolution_time > sla_due:
                    breached += 1
                    
            if t.priority == IncidentPriority.CRITICAL.value:
                critical += 1

        compliance_rate = ((total - breached) / total) * 100.0

        return {
            "total_tickets": total,
            "sla_compliance_rate": round(compliance_rate, 2),
            "breached_tickets": breached,
            "critical_tickets": critical,
            "open_tickets": open_count
        }

    def add_comment(self, ticket_id: int, user: str, comment: str, is_internal: bool = False) -> IncidentTicket:
        """Add a comment to an incident ticket"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket", str(ticket_id))

        ticket.updated_at = self._peru_to_utc(self._now_peru())
        updated = self.incident_repo.update(ticket)

        self._log_audit(
            ticket_id=ticket_id,
            user=user,
            action="COMMENT",
            comment=comment
        )

        return self._to_domain(updated)

    def escalate_ticket(self, ticket_id: int, user: str = "system", reason: str = "SLA breach imminent") -> IncidentTicket:
        """Escalate an incident ticket"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket", str(ticket_id))

        current_status = IncidentStatus(ticket.status)
        if current_status not in [IncidentStatus.IN_PROGRESS, IncidentStatus.ASSIGNED]:
            raise ValidationException(f"No se puede escalar un ticket en estado {current_status.value}")

        from_status = current_status.value
        ticket.status = IncidentStatus.ESCALATED.value
        ticket.updated_at = self._peru_to_utc(self._now_peru())

        updated = self.incident_repo.update(ticket)

        self._log_audit(
            ticket_id=ticket_id,
            user=user,
            action="ESCALATION",
            from_status=from_status,
            to_status=IncidentStatus.ESCALATED.value,
            comment=f"Escalado: {reason}"
        )

        return self._to_domain(updated)

    def link_anomaly(self, ticket_id: int, anomaly_id: int) -> IncidentTicket:
        """Link an anomaly to an existing incident"""
        ticket = self.incident_repo.get_by_id(ticket_id)
        if not ticket:
            raise NotFoundException("Ticket", str(ticket_id))

        anomaly = self.anomaly_repo.get_by_id(anomaly_id)
        if not anomaly:
            raise NotFoundException("Anomaly", str(anomaly_id))

        ticket.anomaly_id = anomaly_id
        ticket.updated_at = self._peru_to_utc(self._now_peru())

        updated = self.incident_repo.update(ticket)
        return self._to_domain(updated)

    def check_and_escalate_sla_breaches(self) -> List[IncidentTicket]:
        """Check for SLA breaches and escalate them (for cron job)"""
        tickets = self.incident_repo.get_all(limit=1000)
        now = self._peru_to_utc(self._now_peru())
        escalated = []

        for t in tickets:
            is_open = t.status not in [
                IncidentStatus.CLOSED.value, IncidentStatus.RESOLVED.value,
                IncidentStatus.REJECTED.value, IncidentStatus.CANCELLED.value,
                IncidentStatus.ESCALATED.value
            ]
            if not is_open:
                continue

            sla_due = t.sla_due_at
            if sla_due is not None and sla_due.tzinfo is None:
                sla_due = sla_due.replace(tzinfo=timezone.utc)

            if sla_due is not None and now > sla_due:
                try:
                    ticket = self.escalate_ticket(t.id, "system", "SLA breach auto-detected")
                    escalated.append(ticket)
                except Exception:
                    pass

        return escalated

    def get_ticket_audit_log(self, ticket_id: int) -> List[Dict[str, Any]]:
        """Get audit log for a ticket"""
        logs = self.audit_repo.get_by_ticket(ticket_id)
        return [{
            "id": log.id,
            "user": log.user,
            "action": log.action,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "from_value": log.from_value,
            "to_value": log.to_value,
            "comment": log.comment,
            "created_at": log.created_at
        } for log in logs]

    def _to_domain(self, model: IncidentTicketModel) -> IncidentTicket:
        return IncidentTicket(
            id=model.id,
            code=model.code,
            anomaly_id=model.anomaly_id,
            dma_id=model.dma_id,
            dma_name=model.dma_name,
            title=model.title,
            description=model.description,
            priority=IncidentPriority(model.priority),
            status=IncidentStatus(model.status),
            assigned_to=model.assigned_to,
            created_at=model.created_at,
            updated_at=model.updated_at,
            sla_due_at=model.sla_due_at,
            resolved_at=model.resolved_at,
            closed_at=model.closed_at,
            response_time_minutes=model.response_time_minutes,
            resolution_time_minutes=model.resolution_time_minutes
        )