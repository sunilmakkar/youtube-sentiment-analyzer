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

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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

    class Config:
        json_schema_extra = {
            "example": {
                "yt_comment_id": "Ugyxk3n1...",
                "author": "John Doe",
                "text": "This video is amazing!",
                "published_at": "2025-10-05T14:30:00Z",
                "like_count": 5,
                "parent_id": None,
            }
        }


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

    class Config:
        json_schema_extra = {
            "example": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "video_id": "abc123",
                "yt_comment_id": "Ugyxk3n1...",
                "author": "Jane Doe",
                "text": "Not my favorite, but interesting topic.",
                "published_at": "2025-10-05T14:45:00Z",
                "like_count": 2,
                "sentiment": "neutral",
            }
        }
