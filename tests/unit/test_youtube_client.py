"""
Unit Test: YouTube Client Service (Stub)
----------------------------------------
These tests verify the behavior of the YouTube client service functions
in `app/services/youtube_client.py`.

Scope:
    - `fetch_video_metadata(video_id)` returns stubbed metadata with
      correct keys and values.
    - `fetch_comments(video_id, org_id)` yields two batches of stubbed
      comments, each containing the required fields.

Notes:
    - This is a pure unit test, no database or API calls are involved.
    - Tests ensure that stub implementations behave predictably for
      higher-level ingestion tasks that depend on them.
"""

import pytest
from datetime import datetime

from app.services import youtube_client


@pytest.mark.asyncio
async def test_fetch_video_metadata_returns_stub():
    """
    Verify `fetch_video_metadata(video_id)` returns a dict
    with the correct stubbed title and channel_id.
    """
    video_id = "abc123"
    result = await youtube_client.fetch_video_metadata(video_id)

    # Structure check
    assert isinstance(result, dict)
    assert "title" in result 
    assert "channel_id" in result 

    # Value checks
    assert result["title"] == f"Stub title for {video_id}"
    assert result["channel_id"] == "stub_channel"


@pytest.mark.asyncio
async def test_fetch_comments_yields_two_batches():
    """
    Verify `fetch_comments(video_id, org_id)` yields exactly two
    batches of stubbed comments, each with the required fields.
    """
    video_id = "abc123"
    org_id = "test_org"

    # Collect all comment batches
    batches = []
    async for batch in youtube_client.fetch_comments(video_id, org_id):
        batches.append(batch)

    # Should yield exactly two batches
    assert len(batches) == 2

    # Each batch should be a list of dicts with expected fields
    for batch in batches:
        assert isinstance(batch, list)
        assert len(batch) >= 1
        for comment in batch:
            assert isinstance(comment, dict)
            assert comment["yt_comment_id"].startswith(f"{org_id}_{video_id}_c")
            assert "text" in comment
            assert "author" in comment
            assert isinstance(comment["published_at"], datetime)
            assert "like_count" in comment
            assert "parent_id" in comment

        total_comments = sum(len(batch) for batch in batches)
        assert total_comments == 2
