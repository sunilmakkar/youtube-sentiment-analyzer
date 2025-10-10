"""
File: comments.py
Purpose:
    Expose endpoints for retrieving comments associated with YouTube videos.

Key responsibilities:
    - Provide paginated access to comments by video_id.
    - Enforce multi-tenant isolation (org_id from JWT).
    - Support optional sentiment flag (placeholder until analysis results exist).

Related modules:
    - app/db/session.py → database session dependency.
    - app/core/deps.py → provides get_current_user dependency.
    - app/models/comment.py → ORM model for comments.
    - app/schemas/comment.py → response schema (CommentOut).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_session
from app.models.comment import Comment
from app.schemas.comment import CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get(
    "/",
    response_model=list[CommentOut],
    summary="Retrieve comments for a YouTube video",
    response_description="List of comments associated with the specified video",
)
async def get_comments(
    video_id: str = Query(..., description="YouTube video ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of comments to return"),
    offset: int = Query(0, description="Pagination offset"),
    has_sentiment: bool = Query(
        False,
        description="If True, include sentiment placeholder in response",
    ),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
    """
    Retrieve comments for a given video.

    Enforces:
        - Multi-tenant scoping (org_id matches current_user).
        - Pagination (limit + offset).

    Returns:
        list[CommentOut] | list[dict]:
            - CommentOut objects by default.
            - Dicts with additional "sentiment" key if has_sentiment=True.
    """
    q = (
        select(Comment)
        .where(
            Comment.org_id == current_user.org_id,
            Comment.video_id == video_id,
        )
        .offset(offset)
        .limit(limit)
    )

    rows = await db.execute(q)
    results = rows.scalars().all()

    if has_sentiment:
        return [{**c.__dict__, "sentiment": None} for c in results]
    return results
