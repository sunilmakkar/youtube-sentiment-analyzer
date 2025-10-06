"""
File: analytics.py
Purpose:
    Provide analytics endpoints for sentiment trends, distributions,
    and keyword frequencies derived from YouTube comments.

Key responsibilities:
    - Expose pre-computed sentiment trend aggregates.
    - Expose real-time sentiment distribution for a video.
    - Expose top keyword frequencies for a video.
    - Enforce multi-tenant access control via org_id in JWT.

Related modules:
    - app/services/aggregates.py → computes trends + distribution.
    - app/services/keywords.py → extracts and stores keyword stats.
    - app/tasks/aggregate.py → background Celery tasks.
    - app/core/deps.py → provides DB session + authenticated user context.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.models import Video
from app.schemas.auth import CurrentUser
from app.services import aggregates, keywords

router = APIRouter()


async def _resolve_video_uuid(db: AsyncSession, org_id: str, yt_video_id: str) -> str:
    """
    Look up the internal UUID for a given YouTube video ID scoped to an org.
    Raises 404 if not found.
    """
    stmt = (
        select(Video.id)
        .where(Video.org_id == org_id)
        .where(Video.yt_video_id == yt_video_id)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Video {yt_video_id} not found")
    return row


@router.get("/analytics/sentiment-trend")
async def sentiment_trend(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    window: str = Query("day", description="Aggregation window (e.g., 'day', 'week')"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get sentiment trend aggregates for a video.

    Args:
        video_id (str): External YouTube video ID.
        window (str): Aggregation window granularity ("day" default).
        db (AsyncSession): Async DB session dependency.
        user (CurrentUser): Authenticated user context.

    Returns:
        list[dict]: One entry per time bucket with:
            - window_start: datetime
            - window_end: datetime
            - pos_pct: float
            - neg_pct: float
            - neu_pct: float
            - count: int
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    trend = await aggregates.compute_and_store_trend(
        db, video_uuid, user.org_id, window
    )
    return {"trend": trend}


@router.get("/analytics/distribution")
async def sentiment_distribution(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get overall sentiment distribution for a video.

    Args:
        video_id (str): External YouTube video ID.
        db (AsyncSession): Async DB session dependency.
        user (CurrentUser): Authenticated user context.

    Returns:
        dict: {
            "pos_pct": float,
            "neg_pct": float,
            "neu_pct": float,
            "count": int
        }
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    return await aggregates.compute_distribution(db, video_uuid, user.org_id)


@router.get("/analytics/keywords")
async def get_keywords(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    top_k: int = Query(25, description="Number of top keywords to return"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get top keyword frequencies for a video.

    Args:
        video_id (str): External YouTube video ID.
        top_k (int): Number of keywords to return (default 25).
        db (AsyncSession): Async DB session dependency.
        user (CurrentUser): Authenticated user context.

    Returns:
        list[dict]: Each entry contains:
            - term: str
            - count: int
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    return await keywords.compute_and_store_keywords(db, video_uuid, user.org_id, top_k)
