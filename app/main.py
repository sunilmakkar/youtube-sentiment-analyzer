from fastapi import FastAPI

from app.api.routes import auth, auth_health, health, ingest, comments
from app.core.logging import init_logging
from app.tasks.celery_app import warmup_model


def create_app() -> FastAPI:
    """Application factory."""
    init_logging()
    app = FastAPI(title="YouTube Sentiment Analyzer", version="0.1.0")

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(auth_health.router)
    app.include_router(ingest.router)
    app.include_router(comments.router)

    return app


# Uvicorn/Gunicorn entrypoint
app = create_app()
