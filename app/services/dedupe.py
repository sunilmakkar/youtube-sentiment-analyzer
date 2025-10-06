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


async def upsert_comments(db: AsyncSession, org_id: str, video_id: str, comments: list[dict]):
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
        - Uses Postgres `INSERT ... ON CONFLICT (org_id, yt_comment_id) DO UPDATE`.
        - Conflict target matches the unique constraint defined in Comment.
        - Updates author, text, published_at, like_count, parent_id if duplicates exist.
        - Commits changes at the end of execution.
    """
    # Normalize payload → always set org_id and video_id from args
    values = []
    for c in comments:
        values.append(
            {
                "org_id": org_id,
                "video_id": video_id,
                "yt_comment_id": c["yt_comment_id"],
                "author": c.get("author"),
                "text": c.get("text"),
                "published_at": c.get("published_at"),
                "like_count": c.get("like_count", 0),
                "parent_id": c.get("parent_id"),
            }
        )

    stmt = insert(Comment).values(values)

    excluded = stmt.excluded

    stmt = stmt.on_conflict_do_update(
        index_elements=["org_id", "yt_comment_id"],
        set_={
            "author": excluded.author,
            "text": excluded.text,
            "published_at": excluded.published_at,
            "like_count": excluded.like_count,
            "parent_id": excluded.parent_id,
        },
    )

    await db.execute(stmt)
    await db.commit()
