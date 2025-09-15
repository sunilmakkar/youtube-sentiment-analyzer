"""
File: comment.py
Purpose:
    Define the Comment model for persisting YouTube video comments.

Key responsibilities:
    - Store raw comment data ingested from YouTube API (via Celery tasks).
    - Support multi-tenancy via org_id.
    - Enforce uniqueness of comments within an org by (org_id, yt_comment_id).
    - Provide base schema for later sentiment analysis linkage.

Related modules:
    - app/models/video.py → links each comment to a video.
    - app/tasks/fetch.py → Celery task that fetches and persists comments.
    - app/models/comment_sentiment.py → stores sentiment analysis of comments.
"""


from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, UniqueConstraint
import uuid

from app.db.base import Base


class Comment(Base):
    """
    ORM model mapping for the `comments` table.

    Attributes:
        id (str): Primary key (UUID string).
        org_id (str): Foreign key → orgs.id, ensures tenant scoping.
        video_id (str): Foreign key → videos.id, links to video being commented on.
        yt_comment_id (str): Original YouTube comment ID (external reference).
        author (str | None): Username of the comment’s author (nullable).
        text (str): Comment text body.
        published_at (datetime): Timestamp when the comment was published.
        like_count (int): Number of likes at time of ingestion (default 0).
        parent_id (str | None): Parent comment ID for replies (nullable).
    """
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    yt_comment_id = Column(String, nullable=False)
    author = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    like_count = Column(Integer, default=0)
    parent_id = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("org_id", "yt_comment_id", name="uq_org_comment"),)
