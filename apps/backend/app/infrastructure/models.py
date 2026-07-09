from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.infrastructure.database import Base
from datetime import datetime

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
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
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
    detected_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    pressure_variation = Column(Float, nullable=True)
    flow_variation = Column(Float, nullable=True)
    estimated_loss_volume = Column(Float, nullable=True)
    description = Column(String(255), nullable=True)


class IncidentTicketModel(Base):
    __tablename__ = "incident_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=False)
    dma_id = Column(String(50), ForeignKey("dmas.code"), nullable=False)
    dma_name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=False)
    priority = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="NEW")  # NEW, CLASSIFIED, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, etc.
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sla_due_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    response_time_minutes = Column(Integer, nullable=True)
    resolution_time_minutes = Column(Integer, nullable=True)
