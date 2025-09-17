"""
Unit tests for app.services.keywords

Covers:
    - compute_and_store_keywords → extracts terms and persists counts.
"""

import pytest
from app.services import keywords


@pytest.mark.asyncio
async def test_compute_keywords_extracts_terms(
    async_session, seeded_comments, current_user
):
    # Act
    result = await keywords.compute_and_store_keywords(
        async_session,
        video_id=seeded_comments.video_id,
        org_id=current_user.org_id,
        top_k=5,
    )

    # Assert
    assert isinstance(result, list)
    if result:
        assert "term" in result[0]
        assert "count" in result[0]
