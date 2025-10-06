"""
File: test_analytics.py
Layer: Integration
------------------
Deep integration tests for Analytics routes.

Targets:
    - /analytics/sentiment-trend

Focus:
    - Verify that sentiment trend aggregates are computed correctly.
    - Validate percentages and counts against explicitly seeded data.
    - Ensure multi-tenant org isolation (cross-org access blocked).

Related tests:
    - test_analytics_routes.py → route smoke tests (status + shape only).
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.video import Video
from app.models.comment import Comment
from app.models.comment_sentiment import CommentSentiment
from app.models.org import Org


@pytest.mark.asyncio
async def test_sentiment_trend_correctness(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers,
):
    """
    Verify that `/analytics/sentiment-trend` returns
    correctly computed percentages and counts for seeded comments.
    """
    org_id = auth_headers["org_id"]

    # Seed video under the same org_id as JWT
    video = Video(org_id=org_id, yt_video_id="yt-trend", title="Trend Test Video")
    db_session.add(video)
    await db_session.flush()

    # Seed comments + sentiments
    for yt_cid, label in [("c1", "pos"), ("c2", "neg"), ("c3", "neu")]:
        comment = Comment(
            id=str(uuid.uuid4()),
            org_id=org_id,
            video_id=video.id,
            yt_comment_id=yt_cid,
            author="tester",
            text=f"Comment {label}",
            published_at=datetime.utcnow(),
            like_count=1,
        )
        db_session.add(comment)
        await db_session.flush()

        sentiment = CommentSentiment(
            id=str(uuid.uuid4()),
            org_id=org_id,
            comment_id=comment.id,
            label=label,
            score=0.9,
            model_name="test-model",
            analyzed_at=datetime.utcnow(),
        )
        db_session.add(sentiment)

    await db_session.commit()

    # Call API
    resp = await async_client.get(
        "/analytics/sentiment-trend",
        params={"video_id": "yt-trend", "window": "day"},
        headers=auth_headers["headers"],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "trend" in body
    trend = body["trend"]
    assert len(trend) == 1
    bucket = trend[0]
    assert bucket["count"] == 3
    assert pytest.approx(bucket["pos_pct"], 0.01) == 1 / 3
    assert pytest.approx(bucket["neg_pct"], 0.01) == 1 / 3
    assert pytest.approx(bucket["neu_pct"], 0.01) == 1 / 3


@pytest.mark.asyncio
async def test_sentiment_trend_wrong_org_isolation(
    async_client: AsyncClient,
    db_session: AsyncSession,
    auth_headers,
):
    """
    Ensure querying another org’s video returns 404 (multi-tenancy isolation).
    """
    # Create a separate org + seed a video under it
    other_org = Org(id=str(uuid.uuid4()), name="Other Org")
    db_session.add(other_org)
    await db_session.flush()

    video = Video(org_id=other_org.id, yt_video_id="yt-other", title="Other Org Video")
    db_session.add(video)
    await db_session.commit()

    # Call API with current JWT (different org) → expect 404
    resp = await async_client.get(
        "/analytics/sentiment-trend",
        params={"video_id": "yt-other", "window": "day"},
        headers=auth_headers["headers"],
    )
    assert resp.status_code == 404
