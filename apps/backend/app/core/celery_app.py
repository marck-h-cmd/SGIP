import os
from celery import Celery
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "sgip_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.services.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Example beat schedule to pull telemetry every minute
    beat_schedule={
        "fetch-mock-telemetry-every-minute": {
            "task": "app.services.tasks.fetch_telemetry_task",
            "schedule": 60.0,
        }
    }
)
