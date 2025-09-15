"""
File: fetch.py
Task: Fetch YouTube Comments
-----------------------------
This Celery task ingests YouTube video metadata and comments into
the database. It runs asynchronously and is retried on transient errors.

Key responsibilities:
    - Ensure the video exists in the `videos` table (insert or update).
    - Fetch comments from the YouTube client in paginated batches.
    - Upsert comments into the `comments` table with deduplication.
    - Commit the transaction once all inserts are done.

Idempotency:
    - Guaranteed by unique constraint (org_id, yt_comment_id).
    - Existing comments are updated, new ones are inserted.

Related modules:
    - app/services/youtube_client.py → fetches stubbed YouTube metadata/comments.
    - app/services/videos.py → handles video upsert.
    - app/services/dedupe.py → handles comment upsert with dedupe logic.
    - app/models/comment.py → comment schema definition.
"""


from asgiref.sync import async_to_sync
from app.db.session import async_session
from app.services.youtube_client import fetch_comments, fetch_video_metadata
from app.services.dedupe import upsert_comments
from app.services.videos import upsert_video
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="task.fetch_comments",
)
def fetch_comments_task(self, video_id: str, org_id: str):
    """
    Celery entrypoint: Fetch + persist comments for a given video/org.

    Args:
        video_id (str): External YouTube video ID.
        org_id (str): Tenant org identifier.

    Returns:
        dict: {
            "video_id": str,
            "comments_fetched": int
        }
    """
    return async_to_sync(_fetch_comments)(video_id, org_id)


async def _fetch_comments(video_id: str, org_id: str):
    """
    Async worker logic for fetching and persisting comments.

    Steps:
        1. Upsert video metadata into the `videos` table.
        2. Iterate over comments from YouTube client (batched).
        3. Normalize missing fields with defaults.
        4. Upsert comments into the `comments` table.
        5. Commit the transaction once all inserts are complete.

    Args:
        video_id (str): External YouTube video ID.
        org_id (str): Tenant org identifier.

    Returns:
        dict: Summary of ingestion results.
    """
    async with async_session() as session:
        # 1. Ensure the video exists and get its DB UUID
        meta = await fetch_video_metadata(video_id)
        video = await upsert_video(session, org_id, video_id, meta)

        # 2. Fetch comments in batches + persist
        total = 0
        async for batch in fetch_comments(video_id):
            for c in batch:
                c.setdefault("author", "Anonymous")
                c.setdefault("published_at", "1970-01-01T00:00:00Z")
                c.setdefault("like_count", 0)
                c.setdefault("parent_id", None)

            # 🔑 Pass DB UUID, not YouTube ID
            await upsert_comments(session, org_id, video.id, batch)
            total += len(batch)

        # 3. Commit all comment inserts at once
        await session.commit()
        return {"video_id": video_id, "comments_fetched": total}
