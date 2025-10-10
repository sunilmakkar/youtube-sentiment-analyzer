"""
File: health.py
Purpose:
    Provide health and readiness endpoints for the API.

Key responsibilities:
    - /healthz → lightweight liveness probe (always "ok").
    - /readyz → deep readiness probe validating dependencies:
        * Postgres DB
        * Redis
        * Celery workers
        * HuggingFace sentiment model flag

Related modules:
    - app/core/config.py → provides Redis URL and settings.
    - app/db/session.py → database engine for DB checks.
    - app/tasks/celery_app.py → Celery app and ping task.
    - app/services/nlp_sentiment.py → model warmup integration.
"""

import time
import redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine
from app.tasks.celery_app import ping

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/healthz",
    summary="Liveness probe",
    response_description="Returns {'status': 'ok'} if the API is alive.",
)
async def healthz():
    """
    Liveness probe.
    Always returns {"status": "ok"} if the FastAPI app is running.

    Used by:
        - CI/CD pipelines (GitHub Actions)
        - Docker orchestration / Fly.io health checks
    """
    return JSONResponse({"status": "ok"})


@router.get(
    "/readyz",
    summary="Readiness probe",
    response_description="Checks DB, Redis, Celery, and HF model readiness.",
)
async def readyz():
    """
    Readiness probe.

    Performs:
        - DB check with a simple SELECT 1 query.
        - Redis ping to confirm cache/broker availability.
        - Celery ping to confirm worker responsiveness.
        - HuggingFace model warmup flag check via Redis.

    Returns:
        dict: JSON response with overall status and individual checks.

    Example response:
        {
            "status": "ok",
            "checks": {
                "db": {"status": "ok", "latency_ms": 1.2},
                "redis": {"status": "ok", "latency_ms": 0.7},
                "celery": {"status": "ok", "latency_ms": 2.1},
                "hf_model": {"status": "ok", "loaded": true}
            }
        }
    """
    checks = {}
    overall_status = "ok"

    # Database check
    start = time.time()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["db"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except SQLAlchemyError:
        checks["db"] = {"status": "error"}
        overall_status = "degraded"

    # Redis check
    start = time.time()
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = {
            "status": "ok",
            "latency_ms": round((time.time() - start) * 1000, 2),
        }
    except Exception:
        checks["redis"] = {"status": "error"}
        overall_status = "degraded"

    # Celery check
    start = time.time()
    try:
        task = ping.delay()
        result = task.get(timeout=5)
        if result == "pong":
            checks["celery"] = {
                "status": "ok",
                "latency_ms": round((time.time() - start) * 1000, 2),
            }
        else:
            checks["celery"] = {"status": "error"}
            overall_status = "degraded"
    except Exception:
        checks["celery"] = {"status": "error"}
        overall_status = "degraded"

    # HuggingFace model flag check
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        if r.get("hf_model_loaded") == b"true":
            checks["hf_model"] = {"status": "ok", "loaded": True}
        else:
            checks["hf_model"] = {"status": "not_loaded", "loaded": False}
    except Exception:
        checks["hf_model"] = {"status": "error", "loaded": False}
        overall_status = "degraded"

    return {"status": overall_status, "checks": checks}
