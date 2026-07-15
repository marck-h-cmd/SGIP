from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base
from datetime import datetime, timezone

class DMAModel(Base):
    __tablename__ = "dmas"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(50), default="ACTIVE")
    population = Column(Integer, nullable=True)
    description = Column(String(255), nullable=True)

    sensors = relationship("SensorModel", back_populates="dma", cascade="all, delete-orphan")


class SensorModel(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # PRESSURE, FLOW
    unit = Column(String(20), nullable=False)  # MCA, LPS
    status = Column(String(50), default="ACTIVE")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    dma = relationship("DMAModel", back_populates="sensors")


class TelemetryReadingModel(Base):
    __tablename__ = "telemetry_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc))
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    sensor_id = Column(String(50), nullable=False)
    pressure_mca = Column(Float, nullable=False)
    flow_lps = Column(Float, nullable=False)
    source = Column(String(50), default="mock")
    quality_flag = Column(String(50), default="GOOD")  # GOOD, BAD, ANOMALY


class AnomalyModel(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    telemetry_id = Column(Integer, nullable=False)
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    dma_name = Column(String(100), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING")  # PENDING, CONFIRMED, REJECTED, RESOLVED
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    pressure_variation = Column(Float, nullable=True)
    flow_variation = Column(Float, nullable=True)
    estimated_loss_volume = Column(Float, nullable=True)
    description = Column(String(255), nullable=True)


class IncidentTicketModel(Base):
    __tablename__ = "incident_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    dma_name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=False)
    priority = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="NEW")  # NEW, CLASSIFIED, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, etc.
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    sla_due_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    response_time_minutes = Column(Integer, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # ANOMALY, SLA_BREACH, MANUAL
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    dma_name = Column(String(100), nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incident_tickets.id"), nullable=True)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, ACKNOWLEDGED, RESOLVED
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    anomaly = relationship("AnomalyModel")
    incident = relationship("IncidentTicketModel")


class IncidentAuditLogModel(Base):
    __tablename__ = "incident_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("incident_tickets.id"), nullable=False)
    user = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # STATUS_CHANGE, ASSIGNMENT, COMMENT, ESCALATION, RESOLUTION
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=True)
    from_value = Column(Text, nullable=True)
    to_value = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("IncidentTicketModel")
