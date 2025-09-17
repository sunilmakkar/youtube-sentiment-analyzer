"""
Integration tests for /analytics routes.

Covers:
    - /analytics/sentiment-trend
    - /analytics/distribution
    - /analytics/keywords
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sentiment_trend_route(
    async_client: AsyncClient, auth_headers, seeded_comments
):
    """
    Verify that the sentiment trend endpoint responds with a list of
    time-bucketed sentiment percentages for a given video.
    """
    resp = await async_client.get(
        f"/analytics/sentiment-trend?video_id={seeded_comments.id}&window=day",
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "pos_pct" in data[0]


@pytest.mark.asyncio
async def test_distribution_route(
    async_client: AsyncClient, auth_headers, seeded_comments
):
    """
    Verify that the sentiment distribution endpoint responds with
    overall sentiment percentages for a given video.
    """
    resp = await async_client.get(
        f"/analytics/distribution?video_id={seeded_comments.id}",
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "pos_pct" in data and "neg_pct" in data and "neu_pct" in data
    assert sum([data["pos_pct"], data["neg_pct"], data["neu_pct"]]) <= 1.0


@pytest.mark.asyncio
async def test_keywords_route(
    async_client: AsyncClient, auth_headers, seeded_comments
):
    """
    Verify that the keywords endpoint responds with top keyword
    frequencies for a given video.
    """
    resp = await async_client.get(
        f"/analytics/keywords?video_id={seeded_comments.id}&top_k=5",
        headers=auth_headers,
    )

    assert resp.status_code == 200
    data = resp.json()
    if data:
        assert "term" in data[0]
        assert "count" in data[0]
