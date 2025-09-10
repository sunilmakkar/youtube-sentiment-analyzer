from fastapi import FastAPI
from app.api.routes import health
from app.core.logging import init_logging

def create_app() -> FastAPI:
    """Application factory."""
    init_logging()
    app = FastAPI(title="YouTube Sentiment Analyzer", version="0.1.0")

    # Include routers
    app.include_router(health.router)

    return app

# Uvicorn/Gunicorn entrypoint
app = create_app()