from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.core.deps import get_current_user
from app.models.comment import Comment
from app.schemas.comment import CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/", response_model=list[CommentOut])
async def get_comments(
    video_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = 0,
    has_sentiment: bool = False,  # kept for API UX, but ignored until sentiment exists
    db: AsyncSession = Depends(get_session),
    current_user=Depends(get_current_user),
):
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
    results = rows.scalars().all()  # return Comment objects

    # if has_sentiment is requested, add a placeholder key
    if has_sentiment:
        return [
            {**c.__dict__, "sentiment": None} for c in results
        ]
    return results
