"""
File: sentiment_aggregate.py
Purpose:
    Define the SentimentAggregate model for storing pre-computed sentiment
    distributions over time windows (e.g., daily trend).

Key responsibilities:
    - Persist aggregate statistics of comment sentiments for a given video.
    - Support analytics endpoints like sentiment-trend and distribution.
    - Ensure tenant scoping with org_id for multi-tenancy.
    - Enforce uniqueness of aggregates per (org_id, video_id, window range).

Related modules:
    - app/models/video.py → aggregates reference videos.
    - app/models/comment_sentiment.py → source data for aggregation.
    - app/tasks/aggregate.py → Celery task that computes and stores aggregates.

Schema:
    sentiment_aggregates
    ┌────────────┬──────────────┬────────────┬───────────────┬───────────────┬─────────────┬─────────────┬────────────┐
    │ id (PK)    │ org_id (FK)  │ video_id   │ window_start  │ window_end    │ pos_pct     │ neg_pct     │ neu_pct    │
    ├────────────┼──────────────┼────────────┼───────────────┼───────────────┼─────────────┼─────────────┼────────────┤
    │ count      │ created_at   │
    └────────────┴──────────────┴────────────┴───────────────┴───────────────┴─────────────┴─────────────┴────────────┘
"""


import uuid
from sqlalchemy import Column, DateTime, String, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class SentimentAggregate(Base):
    """
    ORM model mapping for the `sentimental_aggregates` table.

    Attributes:
        id (str): Primary key (UUID string)
        org_id (str): Foreign key → orgs.id, ensures tenant scoping.
        video_id (str): Foreign key → videos.id, links aggregates to a video.
        window_start (datetime): Beginning of the time window (inclusive).
        window_end (datetime): End of the time window (exclusive).
        pos_pct (float): Percentage of positive comments in the window.
        neg_pct (float): Percentage of negative comments in the window.
        neu_pct (float): Percentage of neutral comments in the window.
        count (int): Total number of comments analyzed in the window.
        created_at (datetime): Row creation timestamp.
    """
    __tablename__ = "sentiment_aggregates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    pos_pct = Column(Float, nullable=False)
    neg_pct = Column(Float, nullable=False)
    neu_pct = Column(Float, nullable=False)
    count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "video_id", "window_start", "window_end", name="uq_org_video_window"),
    )