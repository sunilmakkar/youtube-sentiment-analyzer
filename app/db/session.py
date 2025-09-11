from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with SessionLocal() as session:
        yield session