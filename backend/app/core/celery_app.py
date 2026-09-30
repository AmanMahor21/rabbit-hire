from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ✅ Added include=['app.tasks.hire_tasks'] so Celery knows where the tasks are
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
