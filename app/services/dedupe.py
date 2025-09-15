from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment

async def upsert_comments(db: AsyncSession, org_id, video_id, comments: list[dict]):
    stmt = insert(Comment).values([
        {
            "org_id": org_id,
            "video_id": video_id,
            **c
        }
        for c in comments
    ])
    stmt = stmt.on_conflict_do_update(
        index_elements=["org_id", "yt_comment_id"],
        set_={
            "author": stmt.excluded.author,
            "text": stmt.excluded.text,
            "published_at": stmt.excluded.published_at,
            "like_count": stmt.excluded.like_count,
            "parent_id": stmt.excluded.parent_id,
        },
    )
    await db.execute(stmt)
    await db.commit()