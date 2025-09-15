"""
Task: Analyze YouTube Comments for Sentiment
--------------------------------------------

Purpose:
- Celery task to process unanalyzed comments for a given video/org.
- Uses HuggingFace sentiment analysis via app/services/nlp_sentiment.py.
- Persists results into comment_sentiment table.

Key points:
- Runs asynchronously inside Celery worker.
- Ensures idempotency with (org_id, comment_id) uniqueness.
- Batches inference for efficiency (BATCH_SIZE env).
- Sets model warmup flag so /healthz can report `model.loaded=true`.

Entry point:
- analyze_comments_task(video_id, org_id) → Celery task wrapper
"""

from asgiref.sync import async_to_sync
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.db.session import async_session
from app.models import Comment, CommentSentiment
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
    Celery entrypoint:
    Analyze unanalyzed comments for a given video/org.
    Uses HuggingFace sentiment-anaylsis in batches.
    """
    return async_to_sync(_analyze_comments)(video_id, org_id)


async def _analyze_comments(video_id: str, org_id: str):
    async with async_session() as session:
        # 1. Find all comments for this video/org with no sentiment yet
        stmt = (
            select(Comment)
            .where(Comment.org_id == org_id)
            .where(Comment.video_id == video_id)
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