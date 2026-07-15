"""Celery Tasks for SGIP-CAP"""
from app.celery_config import celery_app
from datetime import datetime, timedelta
from app.services.incident_service import IncidentService
from app.services.report_service import ReportService
from app.services.anomaly_service import AnomalyService
from app.services.telemetry_service import TelemetryService
from app.infrastructure.database import db
from app.infrastructure.models import TelemetryReadingModel
from app.core.config import settings


@celery_app.task(bind=True, name='app.tasks.check_sla_breaches')
def check_sla_breaches(self):
    """Check and escalate SLA breaches"""
    try:
        incident_service = IncidentService()
        escalated = incident_service.check_and_escalate_sla_breaches()
        
        return {
            'status': 'success',
            'checked_at': datetime.utcnow().isoformat(),
            'escalated_count': len(escalated),
            'escalated_ids': [t.id for t in escalated]
        }
    except Exception as e:
        self.retry(countdown=60, max_retries=3)
        return {
            'status': 'error',
            'error': str(e),
            'checked_at': datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name='app.tasks.generate_daily_report')
def generate_daily_report(self):
    """Generate daily report and store it"""
    try:
        report_service = ReportService()
        report = report_service.generate_daily_report()
        
        # Store report in database or file system
        # For now, just log it
        print(f"Daily report generated: {report.get('date', 'N/A')}")
        
        return {
            'status': 'success',
            'generated_at': datetime.utcnow().isoformat(),
            'report_date': report.get('date')
        }
    except Exception as e:
        self.retry(countdown=300, max_retries=2)
        return {
            'status': 'error',
            'error': str(e),
            'generated_at': datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, name='app.tasks.generate_weekly_report')
def generate_weekly_report():
    """Generate weekly report"""
    try:
        report_service = ReportService()
        report = report_service.generate_weekly_report()
        
        print(f"Weekly report generated for period: {report.get('period', {})}")
        
        return {
            'status': 'success',
            'generated_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(bind=True, name='app.tasks.cleanup_old_telemetry_readings')
def cleanup_old_telemetry_readings(self):
    """Clean up old telemetry readings (older than 90 days)"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        deleted_count = db.session.query(TelemetryReadingModel).filter(
            TelemetryReadingModel.timestamp < cutoff_date
        ).delete()
        
        db.session.commit()
        
        print(f"Cleaned up {deleted_count} old telemetry readings")
        
        return {
            'status': 'success',
            'cleaned_at': datetime.utcnow().isoformat(),
            'deleted_count': deleted_count
        }
    except Exception as e:
        db.session.rollback()
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(bind=True, name='app.tasks.detect_anomalies_batch')
def detect_anomalies_batch(self):
    """Run batch anomaly detection"""
    try:
        anomaly_service = AnomalyService()
        telemetry_service = TelemetryService()
        
        # Get latest readings
        latest = telemetry_service.get_latest_readings()
        
        anomalies_detected = 0
        for reading in latest:
            # Run anomaly detection for each DMA
            result = anomaly_service.detect_anomalies_for_dma(reading.get('dma_id'))
            if result:
                anomalies_detected += len(result) if isinstance(result, list) else 1
        
        return {
            'status': 'success',
            'detected_at': datetime.utcnow().isoformat(),
            'anomalies_detected': anomalies_detected
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@celery_app.task(name='app.tasks.send_alert_notification')
def send_alert_notification(alert_id: int, user: str):
    """Send alert notification (email, webhook, etc.)"""
    # Placeholder for notification service
    print(f"Sending alert {alert_id} notification to {user}")
    return {'status': 'sent', 'alert_id': alert_id, 'user': user}


@celery_app.task(name='app.tasks.backup_database')
def backup_database():
    """Backup PostgreSQL database"""
    import subprocess
    import os
    from datetime import datetime
    
    try:
        backup_dir = '/backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{backup_dir}/sgip_backup_{timestamp}.sql'
        
        # pg_dump command
        cmd = [
            'pg_dump',
            '-h', os.getenv('DB_HOST', 'localhost'),
            '-p', os.getenv('DB_PORT', '5432'),
            '-U', os.getenv('DB_USER', 'sgip_user'),
            '-d', os.getenv('DB_NAME', 'sgip_db'),
            '-f', backup_file,
            '--format=custom'
        ]
        
        subprocess.run(cmd, check=True, env={**os.environ, 'PGPASSWORD': os.getenv('DB_PASSWORD', '')})
        
        return {
            'status': 'success',
            'backup_file': backup_file,
            'timestamp': timestamp
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }