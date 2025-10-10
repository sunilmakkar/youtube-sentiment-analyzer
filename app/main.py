"""
File: main.py
Application Entrypoint
----------------------
This module bootstraps the FastAPI application using the factory pattern.

Key responsibilities:
    - Initialize structured logging for consistent output (JSON format).
    - Configure the FastAPI app with metadata (title, description, version, contact).
    - Register all API routers (auth, ingest, analytics, health, comments).
    - Expose an ASGI `app` instance for Uvicorn/Gunicorn.

Related modules:
    - app/core/logging.py → initializes structured logging.
    - app/api/routes/* → defines all API endpoints.
    - app/tasks/celery_app.py → Celery integration (workers, warmup tasks).
"""

from fastapi import FastAPI

from app.api.routes import (
    analytics,
    auth,
    auth_health,
    comments,
    health,
    ingest,
)
from app.core.logging import init_logging


def create_app() -> FastAPI:
    """
    Application factory for the YouTube Sentiment Analyzer.

    Returns:
        FastAPI: Configured FastAPI application instance with all routers and metadata.
    """
    init_logging()

    app = FastAPI(
        title="YouTube Sentiment Analyzer API",
        version="1.0.0",
        description=(
            "The **YouTube Sentiment Analyzer (YTSA)** is a multi-tenant API "
            "that ingests YouTube comments asynchronously, performs sentiment "
            "analysis using a HuggingFace model, and exposes analytics via REST.\n\n"
            "### Core Features\n"
            "- 🧩 Multi-tenant authentication (JWT scoped by org)\n"
            "- ⚙️ Async ingestion and analysis via Celery + Redis\n"
            "- 📊 Sentiment trend and keyword analytics endpoints\n"
            "- 🧠 Health and readiness probes for CI/CD\n"
        ),
        contact={
            "name": "Sunil Makkar",
            "url": "https://github.com/sunilmakkar",
            "email": "sunilmakkar@example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {"name": "auth", "description": "User signup, login, and JWT handling."},
            {"name": "ingest", "description": "Kick off comment ingestion via Celery."},
            {"name": "analytics", "description": "Sentiment trends and keyword data."},
            {"name": "comments", "description": "Retrieve comments for a given video."},
            {"name": "health", "description": "System and service readiness checks."},
            {"name": "authz", "description": "Authz-level health checks for JWT scope."},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
    )

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
