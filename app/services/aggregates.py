"""
File: aggregates.py
Service: Sentiment Aggregation
------------------------------
This service computes and persists sentiment aggregates
for YouTube videos, grouped by a specified time window.

Key responsibilities:
    - Query comment_sentiment records for a given video/org.
    - Group by time window (e.g., daily).
    - Compute percentages of pos/neg/neu labels.
    - Persist results into sentiment_aggregates with uniqueness constraints.

Related modules:
    - app/models/comment_sentiment.py → source data.
    - app/models/sentiment_aggregate.py → target table for aggregates.
    - app/tasks/aggregate.py → Celery entrypoints.
"""

from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.comment_sentiment import CommentSentiment
from app.models.sentiment_aggregate import SentimentAggregate


async def compute_and_store_trend(
    session: AsyncSession, video_id: str, org_id: str, window: str = "day"
) -> list[dict]:
    """
    Compute and persist sentiment aggregates for a video.

    Args:
        session (AsyncSession): Active database session.
        video_id (str): Target video ID (UUID).
        org_id (str): Tenant org identifier.
        window (str): Time window granularity ("day", "week", etc.).

    Returns:
        list[dict]: One entry per time bucket with:
            - window_start: datetime
            - window_end: datetime
            - pos_pct: float
            - neg_pct: float
            - neu_pct: float
            - count: int
    """
    stmt = (
        select(
            func.date_trunc(window, CommentSentiment.analyzed_at).label("bucket"),
            func.count().label("count"),
            func.avg(case((CommentSentiment.label == "pos", 1), else_=0)).label("pos_pct"),
            func.avg(case((CommentSentiment.label == "neg", 1), else_=0)).label("neg_pct"),
            func.avg(case((CommentSentiment.label == "neu", 1), else_=0)).label("neu_pct"),
        )
        .join(
            Comment, Comment.id == CommentSentiment.comment_id
        )  # join through Comment
        .where(CommentSentiment.org_id == org_id)
        .where(Comment.video_id == video_id)  # filter on video_id via Comment
        .group_by("bucket")
        .order_by("bucket")
    )

    result = await session.execute(stmt)
    rows = result.mappings().all()

    aggregates = []
    for r in rows:
        window_start: datetime = r["bucket"]
        window_end: datetime = window_start.replace(hour=23, minute=59, second=59)

        values = dict(
            org_id=org_id,
            video_id=video_id,
            window_start=window_start,
            window_end=window_end,
            pos_pct=float(r["pos_pct"]),
            neg_pct=float(r["neg_pct"]),
            neu_pct=float(r["neu_pct"]),
            count=int(r["count"]),
        )

        insert_stmt = (
            insert(SentimentAggregate)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["org_id", "video_id", "window_start", "window_end"],
                set_=values,
            )
        )
        await session.execute(insert_stmt)
        aggregates.append(values)

    await session.commit()
    return aggregates


async def compute_distribution(
    session: AsyncSession, video_id: str, org_id: str
) -> dict:
    """
    Compute overall sentiment distribution for a video.

    Args:
        session (AsyncSession): Active database session.
        video_id (str): Target video ID (UUID).
        org_id (str): Tenant org identifier.

    Returns:
        dict: {
            "pos_pct": float,
            "neg_pct": float,
            "neu_pct": float,
            "count": int
        }
    """
    stmt = (
        select(CommentSentiment.label, func.count().label("count"))
        .join(
            Comment, Comment.id == CommentSentiment.comment_id
        )  # join through Comment
        .where(CommentSentiment.org_id == org_id)
        .where(Comment.video_id == video_id)  # filter on video_id via Comment
        .group_by(CommentSentiment.label)
    )
    result = await session.execute(stmt)
    rows = result.mappings().all()

    total = sum(r["count"] for r in rows) or 1

    return {
        "pos_pct": next((r["count"] / total for r in rows if r["label"] == "pos"), 0.0),
        "neg_pct": next((r["count"] / total for r in rows if r["label"] == "neg"), 0.0),
        "neu_pct": next((r["count"] / total for r in rows if r["label"] == "neu"), 0.0),
        "count": total,
    }
