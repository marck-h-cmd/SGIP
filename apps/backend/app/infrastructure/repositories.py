from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.infrastructure.models import DMAModel, SensorModel, TelemetryReadingModel, AnomalyModel, IncidentTicketModel, AlertModel, IncidentAuditLogModel

class DMARepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> Optional[DMAModel]:
        return self.db.query(DMAModel).filter(DMAModel.code == code).first()

    def get_all(self) -> List[DMAModel]:
        return self.db.query(DMAModel).all()

    def create(self, dma: DMAModel) -> DMAModel:
        self.db.add(dma)
        self.db.commit()
        self.db.refresh(dma)
        return dma


class SensorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> Optional[SensorModel]:
        return self.db.query(SensorModel).filter(SensorModel.code == code).first()

    def get_by_dma(self, dma_id: str) -> List[SensorModel]:
        return self.db.query(SensorModel).filter(SensorModel.dma_id == dma_id).all()

    def create(self, sensor: SensorModel) -> SensorModel:
        self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor


class TelemetryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_latest(self, dma_id: Optional[str] = None) -> List[TelemetryReadingModel]:
        query = self.db.query(TelemetryReadingModel)
        if dma_id:
            query = query.filter(TelemetryReadingModel.dma_id == dma_id)
        # Group by sensor or just order by timestamp desc
        # Let's get the absolute latest readings
        return query.order_by(desc(TelemetryReadingModel.timestamp)).limit(10).all()

    def get_history(self, dma_id: str, start: datetime, end: datetime, limit: int = 1000) -> List[TelemetryReadingModel]:
        return self.db.query(TelemetryReadingModel)\
            .filter(TelemetryReadingModel.dma_id == dma_id)\
            .filter(TelemetryReadingModel.timestamp >= start)\
            .filter(TelemetryReadingModel.timestamp <= end)\
            .order_by(desc(TelemetryReadingModel.timestamp))\
            .limit(limit).all()

    def create(self, reading: TelemetryReadingModel) -> TelemetryReadingModel:
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading


class AnomalyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[AnomalyModel]:
        return self.db.query(AnomalyModel).filter(AnomalyModel.id == id).first()

    def get_recent(self, dma_id: Optional[str] = None, hours: int = 24) -> List[AnomalyModel]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(AnomalyModel).filter(AnomalyModel.detected_at >= cutoff)
        if dma_id:
            query = query.filter(AnomalyModel.dma_id == dma_id)
        return query.order_by(desc(AnomalyModel.detected_at)).all()

    def create(self, anomaly: AnomalyModel) -> AnomalyModel:
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly

    def update(self, anomaly: AnomalyModel) -> AnomalyModel:
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[IncidentTicketModel]:
        return self.db.query(IncidentTicketModel).filter(IncidentTicketModel.id == id).first()

    def get_by_code(self, code: str) -> Optional[IncidentTicketModel]:
        return self.db.query(IncidentTicketModel).filter(IncidentTicketModel.code == code).first()

    def get_all(self, status: Optional[str] = None, dma_id: Optional[str] = None, priority: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[IncidentTicketModel]:
        query = self.db.query(IncidentTicketModel)
        if status:
            query = query.filter(IncidentTicketModel.status == status)
        if dma_id:
            query = query.filter(IncidentTicketModel.dma_id == dma_id)
        if priority:
            query = query.filter(IncidentTicketModel.priority == priority)
        return query.order_by(desc(IncidentTicketModel.created_at)).offset(offset).limit(limit).all()

    def create(self, ticket: IncidentTicketModel) -> IncidentTicketModel:
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def update(self, ticket: IncidentTicketModel) -> IncidentTicketModel:
        self.db.commit()
        self.db.refresh(ticket)
        return ticket


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[AlertModel]:
        return self.db.query(AlertModel).filter(AlertModel.id == id).first()

    def get_active(self, dma_id: Optional[str] = None) -> List[AlertModel]:
        query = self.db.query(AlertModel).filter(AlertModel.status == "ACTIVE")
        if dma_id:
            query = query.filter(AlertModel.dma_id == dma_id)
        return query.order_by(desc(AlertModel.created_at)).all()

    def get_by_anomaly(self, anomaly_id: int) -> Optional[AlertModel]:
        return self.db.query(AlertModel).filter(AlertModel.anomaly_id == anomaly_id).first()

    def get_by_incident(self, incident_id: int) -> Optional[AlertModel]:
        return self.db.query(AlertModel).filter(AlertModel.incident_id == incident_id).first()

    def get_history(self, hours: int = 24, dma_id: Optional[str] = None) -> List[AlertModel]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(AlertModel).filter(AlertModel.created_at >= cutoff)
        if dma_id:
            query = query.filter(AlertModel.dma_id == dma_id)
        return query.order_by(desc(AlertModel.created_at)).all()

    def get_all(self) -> List[AlertModel]:
        return self.db.query(AlertModel).order_by(desc(AlertModel.created_at)).all()

    def create(self, alert: AlertModel) -> AlertModel:
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def update(self, alert: AlertModel) -> AlertModel:
        self.db.commit()
        self.db.refresh(alert)
        return alert


class IncidentAuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log: IncidentAuditLogModel) -> IncidentAuditLogModel:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_ticket(self, ticket_id: int) -> List[IncidentAuditLogModel]:
        return self.db.query(IncidentAuditLogModel).filter(
            IncidentAuditLogModel.ticket_id == ticket_id
        ).order_by(IncidentAuditLogModel.created_at).all()
