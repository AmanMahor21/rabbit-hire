# backend/app/core/celery_app.py
from celery import Celery
from app.core.config import settings

REDIS_URL = settings.REDIS_URL

celery = Celery(
    "talent",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.hire_tasks", "app.tasks.ingest_tasks"]
)

celery.conf.update(
    task_track_started=True,
    task_time_limit=300,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
