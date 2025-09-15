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


@celery_app.task(name="task.warmup_model")
def warmup_model():
    """
    Force-load the HuggingFace sentiment model in this worker.

    Purpose:
    - Ensures the model pipeline is initialized once after deploy.
    - Makes /healthz report {"hf_model": {"status": "ok", "loaded": true}}.
    - Avoids cold-start latency on the first real sentiment task.

    Usage:
        warmup_model.delay().get(timeout=30)
    """
    from app.services import nlp_sentiment
    import redis
    from app.core.config import settings

    # Run once with a dummy input to trigger lazy loading
    nlp_sentiment.analyze_batch(["warmup"])

    # Store shared flag in Redis
    r = redis.Redis.from_url(settings.REDIS_URL)
    r.set("hf_model_loaded", "true")

    return {"model_loaded": nlp_sentiment.is_model_loaded()}