"""
File: keyword.py
Purpose:
    Define the Keyword model for persisting extracted keyword frequencies
    from comments of a specific video.

Key responsibilities:
    - Store top keywords used in comments for each video.
    - Support analytics endpoints like keywords ranking.
    - Ensure tenant scoping with org_id for multi-tenancy.
    - Enforce uniqueness of keyword entries per (org_id, video_id, term).

Related modules:
    - app/models/video.py → keywords reference videos.
    - app/models/comment.py → source text for keyword extraction.
    - app/tasks/aggregate.py → Celery task that computes and stores keywords.

Schema:
    keywords
    ┌────────────┬──────────────┬────────────┬──────────────┬─────────────┬───────────────┐
    │ id (PK)    │ org_id (FK)  │ video_id   │ term         │ count       │ last_updated_at │
    └────────────┴──────────────┴────────────┴──────────────┴─────────────┴───────────────┘
"""


import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class Keyword(Base):
    """
    ORM model mapping for the `keywords` table.

    Attributes:
        id (str): Primary key (UUID string).
        org_id (str): Foreign key -> orgs.id, ensures tenant scoping.
        video_id (str): Foreign key -> videos.id, links keyword stats to a video.
        term (str): Keyword/term extracted from comments.
        count (int): Frequency of the keyword across comments.
        last_updated_at (datetime): Timestamp when the keyword count was last refreshed.
    """
    __tablename__ = "keywords"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    term = Column(String, nullable=False)
    count = Column(Integer, nullable=False)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("org_id", "video_id", "term", name="uq_org_video_term"),
    )