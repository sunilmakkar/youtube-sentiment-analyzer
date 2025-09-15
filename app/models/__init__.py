"""
File: __init__.py
Purpose:
    Central export hub for all SQLAlchemy ORM models.

Key responsibilities:
    - Collect and re-export all model classes so they can be imported cleanly
      from `app.models` instead of from individual files.
    - Provides a single source of truth for model imports across the app.

Related modules:
    - app/db/base.py → provides declarative Base used by all models.
    - app/db/session.py → manages DB engine + session lifecycle.
    - Alembic migrations → auto-detect schema changes across these models.
"""


from .membership import Membership
from .org import Org
from .user import User
from .comment import Comment
from .video import Video
from .comment_sentiment import CommentSentiment

__all__ = ["Org", "User", "Membership", "Comment", "Video", "CommentSentiment"]
