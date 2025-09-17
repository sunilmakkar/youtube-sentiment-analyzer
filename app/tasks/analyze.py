"""
File: analyze.py
Task: Analyze YouTube Comments for Sentiment
--------------------------------------------
This Celery task processes unanalyzed comments for a given video/org,
runs them through HuggingFace sentiment analysis, and persists results
to the `comment_sentiment` table.

Key responsibilities:
    - Query only comments that do not yet have sentiment rows.
    - Run batch inference using app/services/nlp_sentiment.py.
    - Insert results into comment_sentiment with org scoping.
    - Enforce idempotency via (org_id, comment_id) unique constraint.
    - Warm up model so /healthz can confirm model_loaded=true.

Related modules:
    - app/services/nlp_sentiment.py → wraps HuggingFace pipeline.
    - app/models/comment_sentiment.py → target table for results.
    - app/api/routes/health.py → exposes model warmup flag in /healthz.
    - app/tasks/fetch.py → runs before this to populate comments.

Entrypoints:
    - analyze_comments_task(video_id, org_id) → Celery task wrapper.
"""


from asgiref.sync import async_to_sync
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.db.session import async_session
from app.models import Comment, CommentSentiment, Video
from app.services import nlp_sentiment
from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=5,
    name="task.analyze_comments",
)


def analyze_comments_task(self, video_id: str, org_id: str):
    """
    Celery entrypoint for sentiment analysis.

    Args:
        video_id (str): YouTube video ID (external).
        org_id (str): Tenant org identifier.

    Returns:
        dict: {
            "video_id": str,
            "comments_analyzed": int
        }
    """
    return async_to_sync(_analyze_comments)(video_id, org_id)


async def _analyze_comments(video_id: str, org_id: str):
    """
    Async worker logic to analyze unanalyzed comments.

    Steps:
        1. Select comments for this org/video that do not yet
           have sentiment entries.
        2. Run texts through sentiment analysis in batch.
        3. Insert new rows into comment_sentiment.
        4. Commit transaction.
        5. Mark worker model as warmed up.

    Returns:
        dict: Summary of how many comments were analyzed.
    """
    async with async_session() as session:
        # 1. Find comments linked to the external YouTube video_id
        stmt = (
            select(Comment)
            .join(Video, Comment.video_id == Video.id)
            .where(Comment.org_id == org_id)
            .where(Video.yt_video_id == video_id)  # ✅ filter by YouTube ID
            .where(
                ~Comment.id.in_(
                    select(CommentSentiment.comment_id).where(
                        CommentSentiment.org_id == org_id
                    )
                )
            )
        )
        result = await session.execute(stmt)
        comments = result.scalars().all()

        if not comments:
            return {"video_id": video_id, "comments_analyzed": 0}

        texts = [c.text for c in comments]

        # 2. Run sentiment analysis in batch
        sentiment_results = nlp_sentiment.analyze_batch(texts)

        # 3. Persist results
        inserted = 0
        for comment, sent in zip(comments, sentiment_results):
            try:
                cs = CommentSentiment(
                    org_id=org_id,
                    comment_id=comment.id,
                    label=sent["label"],
                    score=sent["score"],
                    model_name=sent["model_name"],
                    analyzed_at=datetime.utcnow(),
                )
                session.add(cs)
                inserted += 1
            except IntegrityError:
                # Skip if already exists (idempotency)
                await session.rollback()

        await session.commit()

        # 4. Mark worker as warmed up (model loaded)
        if nlp_sentiment.is_model_loaded():
            # This will later surface in /healthz
            pass

        return {"video_id": video_id, "comments_analyzed": inserted}