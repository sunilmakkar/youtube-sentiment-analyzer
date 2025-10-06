"""
File: video.py
Purpose:
    Define the Video model representing YouTube videos ingested into the platform.

Key responsibilities:
    - Store metadata about YouTube videos per tenant (org).
    - Support comment ingestion and later sentiment analysis.
    - Enforce uniqueness of YouTube video IDs within an org (multi-tenancy).

Related modules:
    - app/models/org.py → org_id foreign key ensures tenant scoping.
    - app/models/comment.py → comments reference videos.
    - app/tasks/fetch.py → inserts videos on first comment ingestion.
    - app/tasks/analyze.py → updates `last_analyzed_at` after processing.

Schema:
    videos
    ┌────────────┬──────────────┬──────────────┬────────────┬────────────┐
    │ id (PK)    │ org_id (FK)  │ yt_video_id  │ title      │ channel_id │
    ├────────────┼──────────────┼──────────────┼────────────┼────────────┤
    │ fetched_at │ last_analyzed_at │ created_at │ updated_at │
    └────────────┴──────────────┴──────────────┴────────────┴────────────┘
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class Video(Base):
    """
    ORM model mapping for the `videos` table.

    Attributes:
        id (str): Primary key (UUID string).
        org_id (str): Foreign key to `orgs.id` for tenant scoping.
        yt_video_id (str): Raw YouTube video identifier.
        title (str): Title of the video (from YouTube metadata).
        channel_id (str): ID of the channel that published the video.
        fetched_at (datetime): Timestamp when comments were last fetched.
        last_analyzed_at (datetime): Timestamp when sentiment analysis was last run.
        created_at (datetime): Row creation time (server default).
        updated_at (datetime): Row update time (auto-updated on change).
    """

    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    yt_video_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    channel_id = Column(String, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("org_id", "yt_video_id", name="uq_video_per_org"),
    )
