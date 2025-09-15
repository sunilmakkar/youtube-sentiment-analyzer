"""
File: youtube_client.py
Service: YouTube API Client (Stub)
----------------------------------
This service provides async helpers to fetch YouTube video metadata
and comments. In production, these functions should call the official
YouTube Data API v3. For development and testing, they currently
return stubbed/fake data.

Key responsibilities:
    - Fetch video metadata (title, channel_id).
    - Fetch comments in batches, simulating paginated API results.

Related modules:
    - app/tasks/fetch.py → uses these functions during ingestion.
    - app/services/videos.py → consumes metadata to upsert videos.
    - app/services/dedupe.py → consumes comments for upsert.
"""


from datetime import datetime
import asyncio

async def fetch_video_metadata(video_id: str) -> dict:
    """
    Fetch metadata for a given YouTube video.

    Args:
        video_id (str): YouTube video ID.

    Returns:
        dict: Metadata with keys:
            {
                "title": str,
                "channel_id": str,
            }

    Note:
        - Currently returns stub values.
        - Replace with YouTube Data API call in production.
    """
    return {"title": f"Stub title for {video_id}", "channel_id": "stub_channel"}

async def fetch_comments(video_id: str, page_token: str = None):
    """
    Fetch comments for a given YouTube video, yielding them in batches.

    Args:
        video_id (str): YouTube video ID.
        page_token (str, optional): Token for pagination.

    Yields:
        list[dict]: Each batch is a list of comment dictionaries:
            {
                "yt_comment_id": str,
                "text": str,
                "author": str,
                "published_at": datetime,
                "like_count": int,
                "parent_id": Optional[str],
            }

    Note:
        - Simulates two pages of results with a short sleep.
        - Replace with real API pagination logic in production.
    """

    for i in range(2):
        await asyncio.sleep(0.05)
        yield [{
            "yt_comment_id": f"{video_id}_c{i}",
            "text": "Great video!",
            "author": "stub_user",
            "published_at": datetime.utcnow(),  # ✅ required field
            "like_count": 0,
            "parent_id": None,
        }]
