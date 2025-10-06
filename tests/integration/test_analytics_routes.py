"""
File: test_analytics_routes.py
Layer: Integration
------------------
Integration tests for the Analytics API routes.

Targets:
    - /analytics/sentiment-trend
    - /analytics/distribution
    - /analytics/keywords

Key aspects validated:
    - Endpoints return HTTP 200 for seeded test data.
    - Responses contain correct JSON structure and required fields.
    - Routes enforce external YouTube video ID (`yt_video_id`) contract.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_sentiment_trend_route(
    async_client: AsyncClient, auth_headers, seeded_sentiments_for_auth
):
    """
    Verify that `/analytics/sentiment-trend` returns a list of
    time-bucketed sentiment percentages for a given video.
    """
    resp = await async_client.get(
        f"/analytics/sentiment-trend?video_id={seeded_sentiments_for_auth.yt_video_id}&window=day",
        headers=auth_headers["headers"],
    )

    assert resp.status_code == 200
    data = resp.json()

    assert "trend" in data
    assert isinstance(data["trend"], list)

    if data["trend"]:
        row = data["trend"][0]
        assert "pos_pct" in row
        assert "neg_pct" in row
        assert "neu_pct" in row
        assert "count" in row


@pytest.mark.asyncio
async def test_distribution_route(
    async_client: AsyncClient, auth_headers, seeded_sentiments_for_auth
):
    """
    Verify that `/analytics/distribution` returns overall sentiment
    percentages for a given video.
    """
    resp = await async_client.get(
        f"/analytics/distribution?video_id={seeded_sentiments_for_auth.yt_video_id}",
        headers=auth_headers["headers"],
    )

    assert resp.status_code == 200
    data = resp.json()

    assert "pos_pct" in data
    assert "neg_pct" in data
    assert "neu_pct" in data
    assert "count" in data

    assert 0.0 <= data["pos_pct"] <= 1.0
    assert 0.0 <= data["neg_pct"] <= 1.0
    assert 0.0 <= data["neu_pct"] <= 1.0


@pytest.mark.asyncio
async def test_keywords_route(
    async_client: AsyncClient, auth_headers, seeded_sentiments_for_auth
):
    """
    Verify that `/analytics/keywords` returns a list of top keyword
    frequencies for a given video.
    """
    resp = await async_client.get(
        f"/analytics/keywords?video_id={seeded_sentiments_for_auth.yt_video_id}&top_k=5",
        headers=auth_headers["headers"],
    )

    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)

    if data:
        row = data[0]
        assert "term" in row
        assert "count" in row
