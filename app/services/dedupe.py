"""
File: dedupe.py
Purpose:
    Provide helper functions to deduplicate and upsert YouTube comments.

Key responsibilities:
    - Insert new comments into the database.
    - Update existing comments in case of conflict (same org_id + yt_comment_id).
    - Ensure idempotent ingestion when fetching comments in batches.

Related modules:
    - app/models/comment.py → defines the Comment table with unique constraints.
    - app/tasks/fetch.py → calls upsert_comments during ingestion pipeline.
"""


from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import Comment

async def upsert_comments(db: AsyncSession, org_id, video_id, comments: list[dict]):
    """
    Insert or update a batch of YouTube comments for a given org and video.

    Args:
        db (AsyncSession): Active SQLAlchemy async session.
        org_id (str): Organization (tenant) ID for scoping.
        video_id (str): Internal DB ID of the associated video.
        comments (list[dict]): Raw comment dictionaries, e.g.:
            {
                "yt_comment_id": "abc123",
                "author": "user",
                "text": "Great video!",
                "published_at": <datetime>,
                "like_count": 10,
                "parent_id": None,
            }

    Behavior:
        - Uses Postgres `INSERT ... ON CONFLICT DO UPDATE`.
        - Conflict target: (org_id, yt_comment_id).
        - Updates fields like author, text, published_at, like_count, parent_id if duplicates exist.
        - Commits changes at the end of execution.
    """
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