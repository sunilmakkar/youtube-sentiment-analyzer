from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.video import Video
import sqlalchemy as sa

async def upsert_video(db: AsyncSession, org_id: str, video_id: str, meta: dict) -> Video:
    """
    Insert or update a video for this org, returning the persisted Video row. 
    Guarantees the row is committed so its UUID can be used as FK.
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
