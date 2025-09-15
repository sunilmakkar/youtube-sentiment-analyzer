from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CommentIn(BaseModel):
    yt_comment_id: str
    author: Optional[str] = None
    text: str
    published_at: datetime
    like_count: int = 0
    parent_id: Optional[str] = None


class CommentOut(CommentIn):
    id: str
    video_id: str
    sentiment: Optional[str] = None
