import asyncio

from app.db.session import async_session
from app.models.video import Video
from app.services.youtube_client import fetch_comments, fetch_video_metadata
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="task.fetch_comments",
)
def fetch_comments_task(self, video_id: str, org_id: str):
    return asyncio.run(_fetch_comments(video_id, org_id))


async def _fetch_comments(video_id: str, org_id: str):
    async with async_session() as session:
        # Upsert video metadata
        meta = await fetch_video_metadata(video_id)
        video = Video(
            org_id=org_id,
            yt_video_id=video_id,
            title=meta["title"],
            channel_id=meta["channel_id"],
        )
        await session.merge(video)  # merge = upsert by PK/UC
        await session.commit()

        all_comments = []
        async for batch in fetch_comments(video_id):
            all_comments.extend(batch)
            # TODO: Insert into comments table (Phase 4)

        return {"video_id": video_id, "comments_fetched": len(all_comments)}
