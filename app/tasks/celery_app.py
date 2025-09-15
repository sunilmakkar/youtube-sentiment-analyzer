"""
File: celery_app.py
Service: Celery Application
----------------------------
This module configures the Celery application instance used for 
background tasks (e.g., comment ingestion, sentiment analysis).

Key responsibilities:
    - Define the central Celery `celery_app` object.
    - Configure broker and result backend from environment variables.
    - Auto-discover tasks within `app/tasks/`.
    - Provide simple health-check (`ping`) and warmup tasks.

Related modules:
    - app/tasks/fetch.py → fetch YouTube comments into DB.
    - app/tasks/analyze.py → analyze comments for sentiment.
    - app/services/nlp_sentiment.py → HuggingFace sentiment model.
    - app/api/routes/health.py → monitors worker + model readiness.
"""


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
    """
    Simple health-check task.

    Returns:
        str: Always returns "pong" if worker is alive.
    """
    return "pong"


@celery_app.task(name="task.warmup_model")
def warmup_model():
    """
    Celery task to force-load the HuggingFace sentiment model.

    Purpose:
        - Ensures the model pipeline is initialized once after deploy.
        - Allows /healthz to report:
            {"hf_model": {"status": "ok", "loaded": true}}
        - Eliminates cold-start latency for the first real analysis task.

    Returns:
        dict: {
            "model_loaded": bool  # True if pipeline is initialized
        }

    Usage:
        >>> warmup_model.delay().get(timeout=30)
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