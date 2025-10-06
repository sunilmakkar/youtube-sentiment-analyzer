"""
File: videos.py
Service: Video Upsert
----------------------
This service provides helper functions to insert or update
YouTube video metadata for a given organization (tenant).

Key responsibilities:
    - Ensure each org/video pair is unique (org_id + yt_video_id).
    - Insert new videos or update existing ones with latest metadata.
    - Guarantee the video row is committed so its UUID can be reused
      as a foreign key for related tables (e.g., comments).

Related modules:
    - app/models/video.py → defines the Video table schema.
    - app/tasks/fetch.py → calls `upsert_video` during ingestion.
"""

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video


async def upsert_video(
    db: AsyncSession, org_id: str, video_id: str, meta: dict
) -> Video:
    """
    Insert or update a video for this org, returning the persisted Video row.

    Args:
        db (AsyncSession): Active SQLAlchemy async session.
        org_id (str): Tenant organization ID for scoping.
        video_id (str): External YouTube video ID.
        meta (dict): Metadata dictionary with keys:
            {
                "title": str,
                "channel_id": str,
            }

    Returns:
        Video: SQLAlchemy Video ORM object with a guaranteed UUID `id`.

    Behavior:
        - Uses Postgres `INSERT ... ON CONFLICT DO UPDATE`.
        - Conflict target: (org_id, yt_video_id).
        - Updates `title`, `channel_id`, and `last_analyzed_at` on conflict.
        - Commits the transaction and re-fetches the full Video row
          to return a fully populated ORM instance.
    """
    insert_stmt = insert(Video).values(
        org_id=org_id,
        yt_video_id=video_id,
        title=meta["title"],
        channel_id=meta["channel_id"],
    )

    stmt = insert_stmt.on_conflict_do_update(
        index_elements=["org_id", "yt_video_id"],
        set_={
            "title": insert_stmt.excluded.title,
            "channel_id": insert_stmt.excluded.channel_id,
            "last_analyzed_at": sa.func.now(),
        },
    ).returning(Video.id)

    result = await db.execute(stmt)
    video_pk = result.scalar_one()

    # Commit
    await db.commit()

    # Load the full Video object so we can access video.id, title, etc.
    result = await db.execute(select(Video).where(Video.id == video_pk))
    return result.scalar_one()
