"""
File: main.py
Application Entrypoint
----------------------
This module bootstraps the FastAPI application using the factory pattern.

Key responsibilities:
    - Initialize structured logging for consistent output (JSON format).
    - Configure the FastAPI app with metadata (title, version).
    - Register all API routers (auth, ingest, health, comments).
    - Expose an ASGI `app` instance for Uvicorn/Gunicorn.

Related modules:
    - app/core/logging.py → initializes structured logging.
    - app/api/routes/* → defines all API endpoints.
    - app/tasks/celery_app.py → Celery integration (workers, warmup tasks).
"""

from fastapi import FastAPI

from app.api.routes import (analytics, auth, auth_health, comments, health,
                            ingest)
from app.core.logging import init_logging


def create_app() -> FastAPI:
    """
    Application factory for the YouTube Sentiment Analyzer.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    init_logging()
    app = FastAPI(title="YouTube Sentiment Analyzer", version="0.1.0")

    # Include routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(auth_health.router)
    app.include_router(ingest.router)
    app.include_router(comments.router)
    app.include_router(analytics.router)

    return app


# Uvicorn/Gunicorn entrypoint
app = create_app()
