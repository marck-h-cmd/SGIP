from app.services.telemetry_service import TelemetryService
from app.services.anomaly_service import AnomalyService
from app.services.incident_service import IncidentService
from app.services.kpi_service import KPIService
from app.services.alert_service import AlertService


def get_telemetry_service():
    return TelemetryService()


def get_anomaly_service():
    return AnomalyService()


def get_incident_service():
    return IncidentService()


def get_alert_service():
    return AlertService()


def get_kpi_service(
    telemetry_service=None,
    anomaly_service=None,
    incident_service=None,
):
    if telemetry_service is None:
        telemetry_service = TelemetryService()
    if anomaly_service is None:
        anomaly_service = get_anomaly_service()
    if incident_service is None:
        incident_service = get_incident_service()
    return KPIService(
        telemetry_service=telemetry_service,
        anomaly_service=anomaly_service,
        incident_service=incident_service,
    )