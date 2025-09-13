import pytest
from sqlalchemy import text
from app.db.session import SessionLocal


@pytest.mark.asyncio
async def test_videos_table_exists():
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='videos'")
        )
        cols = [r[0] for r in result]
        assert "id" in cols
        assert "org_id" in cols
        assert "yt_video_id" in cols
