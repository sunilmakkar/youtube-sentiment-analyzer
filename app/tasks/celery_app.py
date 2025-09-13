from celery import Celery
import os

celery_app = Celery(
    "ytsa",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2"),
)

# Auto-discover tasks from app/tasks/
celery_app.autodiscover_tasks(["app.tasks"])

# Explicit import ensures fetch.py tasks always get registered
import app.tasks.fetch

@celery_app.task(name="task.ping")
def ping():
    return "pong"