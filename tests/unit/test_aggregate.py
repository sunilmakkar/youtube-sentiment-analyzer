"""
Unit tests for app.services.aggregates

Covers:
    - compute_distribution → returns expected shape and values.
"""

import pytest
from app.services import aggregates


@pytest.mark.asyncio
async def test_compute_distribution_returns_expected_shape(
    async_session, seeded_comments, current_user
):
    # Act
    result = await aggregates.compute_distribution(
        async_session, video_id=seeded_comments.video_id, org_id=current_user.org_id
    )

    # Assert
    assert set(result.keys()) == {"pos_pct", "neg_pct", "neu_pct", "count"}
    assert 0.0 <= result["pos_pct"] <= 1.0
    assert result["count"] > 0
