"""
File: comment.py
Purpose:
    Define Pydantic schemas for YouTube comments.

Key responsibilities:
    - Input validation for comments (when ingesting).
    - Output formatting for API responses.
    - Optional sentiment field for future enrichment.

Related modules:
    - app/models/comment.py → SQLAlchemy ORM model for DB.
    - app/api/routes/comments.py → returns CommentOut objects.
    - app/tasks/fetch.py → ingests and persists CommentIn.
"""


from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CommentIn(BaseModel):
    """
    Schema for ingesting raw YouTube comment data.
    Used by fetch pipeline before persistence.
    """
    yt_comment_id: str
    author: Optional[str] = None
    text: str
    published_at: datetime
    like_count: int = 0
    parent_id: Optional[str] = None


class CommentOut(CommentIn):
    """
    Schema for returning comments via API.

    Extends CommentIn with:
        - id: Internal UUID for DB row.
        - video_id: Reference to parent video.
        - sentiment: Optional placeholder for enrichment.
    """
    id: str
    video_id: str
    sentiment: Optional[str] = None
