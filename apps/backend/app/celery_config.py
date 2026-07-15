"""Celery Configuration for SGIP-CAP"""
from celery import Celery
from celery.schedules import crontab
import os

# Create Celery app
celery_app = Celery(
    'sgip_cap',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Lima',
    enable_utc=True,
    
    # Task execution settings
    task_always_eager=False,
    task_eager_propagates=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Result settings
    result_expires=3600,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        'check-sla-breaches': {
            'task': 'app.tasks.check_sla_breaches',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
            'options': {'queue': 'default'}
        },
        'generate-daily-report': {
            'task': 'app.tasks.generate_daily_report',
            'schedule': crontab(hour=6, minute=0),  # 6 AM Peru time
            'options': {'queue': 'reports'}
        },
        'generate-weekly-report': {
            'task': 'app.tasks.generate_weekly_report',
            'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Monday 7 AM
            'options': {'queue': 'reports'}
        },
        'cleanup-old-readings': {
            'task': 'app.tasks.cleanup_old_telemetry_readings',
            'schedule': crontab(hour=3, minute=0),  # 3 AM daily
            'options': {'queue': 'maintenance'}
        },
        'detect-anomalies': {
            'task': 'app.tasks.detect_anomalies_batch',
            'schedule': crontab(minute='*/2'),  # Every 2 minutes
            'options': {'queue': 'ml'}
        },
    },
    task_routes={
        'app.tasks.check_sla_breaches': {'queue': 'default'},
        'app.tasks.generate_*_report': {'queue': 'reports'},
        'app.tasks.cleanup_*': {'queue': 'maintenance'},
        'app.tasks.detect_*': {'queue': 'ml'},
    },
    task_default_queue='default',
)

# Auto-discover tasks in the app.tasks module
celery_app.autodiscover_tasks(['app.tasks'])