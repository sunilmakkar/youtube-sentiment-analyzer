from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

# Export session factory for Celery + other async tasks
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# FastAPI dependency
async def get_session():
    async with async_session() as session:
        yield session
