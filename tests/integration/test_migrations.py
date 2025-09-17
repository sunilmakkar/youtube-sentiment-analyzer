"""
Integration Test: Database Migrations
-------------------------------------
This test ensures critical tables exist after running Alembic migrations.

Coverage:
    - videos table → validates required schema columns.
"""


import pytest
from sqlalchemy import text
from app.db.session import async_session


@pytest.mark.asyncio
async def test_videos_table_exists():
    """
    Ensure the "videos" table exists and contains the required columns.
    Validates migration integrity after Alembic upgrade.
    """
    async with async_session() as session:
        result = await session.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='videos'")
        )
        cols = [r[0] for r in result]
        assert "id" in cols
        assert "org_id" in cols
        assert "yt_video_id" in cols
