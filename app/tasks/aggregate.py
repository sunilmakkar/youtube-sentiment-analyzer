"""
File: aggregate.py
Task: Compute Sentiment Aggregates & Keywords
---------------------------------------------
This Celery task module handles background computation of
video-level analytics, including sentiment trends and keyword
frequencies.

Key responsibilities:
    - Aggregate comment_sentiment rows into windowed trends
      (daily, weekly, etc.).
    - Compute overall sentiment distribution for a video.
    - Extract top keywords from comments and persist them
      into the `keywords` table.
    - Ensure idempotency via unique constraints on
      sentiment_aggregates and keywords tables.

Related modules:
    - app/services/aggregates.py → implements trend/distribution queries.
    - app/services/keywords.py → implements keyword extraction + persistence.
    - app/models/sentiment_aggregate.py → schema for aggregates.
    - app/models/keyword.py → schema for keywords.
    - app/api/routes/analytics.py → exposes endpoints for clients.

Entrypoints:
    - compute_sentiment_trend_task(video_id, org_id, window)
    - compute_keywords_task(video_id, org_id, top_k)
"""

from asgiref.sync import async_to_sync

from app.db.session import async_session
from app.services import aggregates, keywords
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="task.compute_sentiment_trend",
)
def compute_sentiment_trend_task(
    self, video_id: str, org_id: str, window: str = "daily"
):
    """
    Celery entrypoint: Compute and persist sentiment aggregates for a video.

    Args:
        video_id (str): External YouTube video ID.
        org_id (str): Tenant org identifier.
        window (str): Aggregation window (default "daily").

    Returns:
        dict : {
            "video_id": str,
            "window": str,
            "aggregates_computed": int
        }
    """
    return async_to_sync(_compute_sentiment_trend)(video_id, org_id, window)


async def _compute_sentiment_trend(video_id: str, org_id: str, window: str):
    """
    Async worker logic to compute sentiment trend aggregates.

    Steps:
        1. Query comment_sentiment for org/video.
        2. Group by requested window (e.g., day).
        3. Insert or update sentiment_aggregates rows.
        4. Commit transaction.

    Returns:
        dict: Summary of how many aggregate rows were computed.
    """
    async with async_session() as session:
        aggregates_computed = await aggregates.compute_and_store_trend(
            session, video_id, org_id, window
        )
        return {
            "video_id": video_id,
            "window": window,
            "aggregates_computed": aggregates_computed,
        }


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="task.compute_keywords",
)
def compute_keywords_task(self, video_id: str, org_id: str, top_k: int = 25):
    """
    Celery entrypoint: Compute and persist top keywords for a video.

    Args:
        video_id (str): External YouTube video ID.
        org_id (str): Tenant org identifier.
        top_k (int): Number of top keywords to store.

    Returns:
        dict: {
            "video_id": str,
            "keywords_computed": int
        }
    """
    return async_to_sync(_compute_keywords)(video_id, org_id, top_k)


async def _compute_keywords(video_id: str, org_id: str, top_k: int):
    """
    Async worker logic to compute keyword frequencies.

    Steps:
        1. Query all comments for org/video.
        2. Tokenize text and count keyword frequencies.
        3. Upsert top_k terms into keywords table.
        4. Commit transaction.

    Returns:
        dict: Summary of how many keywords were computed.
    """
    async with async_session() as session:
        results = await keywords.compute_and_store_keywords(
            session, video_id, org_id, top_k
        )
        return {"video_id": video_id, "keywords_computed": len(results)}
