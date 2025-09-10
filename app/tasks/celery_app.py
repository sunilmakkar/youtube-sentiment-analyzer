from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "ytsa",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Optional: configuration (retries, task serialization, etc)
celery_app.conf.update(
    task_track_started=True,
    task_serializers="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

# Example task
@celery_app.task(name="task.ping")
def ping():
    return "pong"