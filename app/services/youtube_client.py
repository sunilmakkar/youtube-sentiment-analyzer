import asyncio


async def fetch_video_metadata(video_id: str) -> dict:
    # Replace with real YouTube Data API call
    return {"title": f"Stub title for {video_id}", "channel_id": "stub_channel"}


async def fetch_comments(video_id: str, page_token: str = None):
    # Fake two pages
    for i in range(2):
        await asyncio.sleep(0.05)
        yield [{"yt_comment_id": f"{video_id}_c{i}", "text": "Great video!"}]
