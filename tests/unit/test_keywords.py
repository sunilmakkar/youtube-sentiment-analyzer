"""
File: test_keywords.py
Layer: Unit
------------
Unit tests for the Keyword Extraction service.

Targets:
    - compute_and_store_keywords

Key aspects validated:
    - Tokenization and frequency counting of comment text.
    - Persistence of top terms into the Keyword table.
    - Correct return shape ({term, count}).
"""


import pytest
from sqlalchemy import select

from app.services import keywords
from app.models.keyword import Keyword


@pytest.mark.asyncio
async def test_compute_and_store_keywords_extracts_and_persists(
    db_session, seeded_comments_for_auth
):
    """
    It should extract keywords from comments
    persist them into a `keywords` table,
    and return a structured list of {term, count}.
    """
    video = seeded_comments_for_auth
    org_id = video.org_id

    # --- Act ---
    results = await keywords.compute_and_store_keywords(
        db_session,
        video_id=video.id,
        org_id=org_id,
        top_k=5,
    )

    # --- Assert: return shape ---
    assert isinstance(results, list)
    assert all("term" in r and "count" in r for r in results)

    # --- Assert: persisted in DB ---
    rows = (await db_session.execute(select(Keyword))).scalars().all()
    assert len(rows) > 0
    assert all(row.term and row.count >= 1 for row in rows)



@pytest.mark.asyncio
async def test_compute_and_store_keywords_returns_expected_shape(
    db_session, seeded_comments_for_auth
):
    """
    It should return a list of keyword dicts with
    the expected shape ({term, count}) when called
    on seeded comments.
    """
    video = seeded_comments_for_auth
    org_id = video.org_id

    # --- Act ---
    results = await keywords.compute_and_store_keywords(
        db_session,
        video_id=video.id,
        org_id=org_id,
        top_k=5,
    )

    # --- Assert ---
    assert isinstance(results, list)
    if results:
        first = results[0]
        assert "term" in first
        assert "count" in first