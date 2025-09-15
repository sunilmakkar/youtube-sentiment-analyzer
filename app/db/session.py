"""
File: session.py
Purpose:
    Manage database connections and sessions using SQLAlchemy's async engine.

Key responsibilities:
    - Initialize a global async database engine tied to the app’s DATABASE_URL.
    - Provide an async session factory for tasks and Celery workers.
    - Expose a FastAPI dependency (`get_session`) for request-scoped sessions.

Related modules:
    - app/core/config.py → loads DATABASE_URL from environment.
    - app/db/base.py → defines declarative Base for ORM models.
    - app/tasks/* → Celery tasks use async_session for database work.
"""


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Global async engine connected to DATABASE_URL
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

# Session factory for async DB access (used by Celery + background tasks)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevents automatic expiration of objects on commit
)

# FastAPI dependency
async def get_session():
    """
    Yield a database session for the lifespan of a single request.
    
    Usage:
        - Injected via Depends in route handlers.
        - Ensures proper cleanup after the request is processed.
    """
    async with async_session() as session:
        yield session
