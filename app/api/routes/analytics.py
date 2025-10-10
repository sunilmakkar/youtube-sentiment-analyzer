"""
File: analytics.py
Layer: API
-----------
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
    - app/core/deps.py → provides DB session + authenticated user context.
    - app/schemas/analytics.py → defines Pydantic response models.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_session
from app.models import Video
from app.schemas.auth import CurrentUser
from app.schemas.analytics import (
    SentimentTrendResponse,
    SentimentDistributionResponse,
    KeywordsResponse,
)
from app.services import aggregates, keywords

router = APIRouter(tags=["analytics"])


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


@router.get(
    "/analytics/sentiment-trend",
    response_model=SentimentTrendResponse,
    summary="Get sentiment trend for a video",
    response_description="List of time-bucketed sentiment percentages.",
)
async def sentiment_trend(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    window: str = Query("day", description="Aggregation window (e.g., 'day', 'week')"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get sentiment trend aggregates for a video.

    Returns:
        SentimentTrendResponse: One entry per time bucket with:
            - window_start / window_end
            - pos_pct / neg_pct / neu_pct
            - count
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    trend = await aggregates.compute_and_store_trend(
        db, video_uuid, user.org_id, window
    )
    return {"trend": trend}


@router.get(
    "/analytics/distribution",
    response_model=SentimentDistributionResponse,
    summary="Get overall sentiment distribution for a video",
    response_description="Proportional breakdown of sentiments for a video.",
)
async def sentiment_distribution(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get overall sentiment distribution for a video.

    Returns:
        SentimentDistributionResponse: {
            pos_pct, neg_pct, neu_pct, count
        }
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    return await aggregates.compute_distribution(db, video_uuid, user.org_id)


@router.get(
    "/analytics/keywords",
    response_model=KeywordsResponse,
    summary="Get top keyword frequencies for a video",
    response_description="Top N keywords with occurrence counts.",
)
async def get_keywords(
    video_id: str = Query(..., description="Target YouTube video ID (external)"),
    top_k: int = Query(25, description="Number of top keywords to return"),
    db: AsyncSession = Depends(get_session),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Get top keyword frequencies for a video.

    Returns:
        KeywordsResponse: [{ term, count }, ...]
    """
    video_uuid = await _resolve_video_uuid(db, user.org_id, video_id)
    keywords_list = await keywords.compute_and_store_keywords(
        db, video_uuid, user.org_id, top_k
    )
    return {"keywords": keywords_list}
