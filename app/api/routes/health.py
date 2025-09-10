import time
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import redis
from app.core.config import settings
from app.db.session import engine
from app.tasks.celery_app import ping

router = APIRouter()

@router.get("/healthz")
async def healthz():
    checks = {}
    overall_status = "ok"

    # DB
    start = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db"] = {"status": "ok", "latency_ms": round((time.time() - start) * 1000, 2)}
    except SQLAlchemyError:
        checks["db"] = {"status": "error"}
        overall_status = "degraded"

    # Redis
    start = time.time()
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = {"status": "ok", "latency_ms": round((time.time() - start) * 1000, 2)}
    except Exception:
        checks["redis"] = {"status": "error"}
        overall_status = "degraded"

    # Celery
    start = time.time()
    try:
        task = ping.delay()
        result = task.get(timeout=5)
        if result == "pong":
            checks["celery"] = {"status": "ok", "latency_ms": round((time.time() - start) * 1000, 2)}
        else:
            checks["celery"] = {"status": "error"}
            overall_status = "degraded"
    except Exception:
        checks["celery"] = {"status": "error"}
        overall_status = "degraded"

    # HF model (lazy load placeholder)
    checks["hf_model"] = {"status": "not_loaded"}

    return {"status": overall_status, "checks": checks}
