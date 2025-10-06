"""
File: test_dedupe.py
Purpose:
    Unit tests for app/services/dedupe.py.

Key responsibilities tested:
    - Ensure that upsert_comments inserts new YouTube comments into the database.
    - Ensure that when a comment with the same (org_id, yt_comment_id) is inserted again,
      the record is updated rather than duplicated.
    - Confirm that Postgres `ON CONFLICT (org_id, yt_comment_id)` works as intended.

Fixtures used:
    - db_session: async SQLAlchemy session bound to the test database.
    - seeded_comments_for_auth: provides a seeded Video row for a valid org_id/video_id.
"""

import pytest
from sqlalchemy import select
from datetime import datetime

from app.services import dedupe
from app.models.comment import Comment


@pytest.mark.asyncio
async def test_upsert_comments_inserts_and_updates(db_session, seeded_comments_for_auth):
    video = seeded_comments_for_auth
    org_id = video.org_id
    video_id = video.id
    yt_comment_id = "abc123"

    # First insert
    comments = [
        {
            "yt_comment_id": yt_comment_id,
            "author": "user1",
            "text": "Great video!",
            "published_at": datetime.utcnow(),
            "like_count": 10,
        }
    ]
    await dedupe.upsert_comments(db_session, org_id, video_id, comments)

    row = (
        await db_session.execute(
            select(Comment).where(
                Comment.org_id == org_id,
                Comment.video_id == video_id,
                Comment.yt_comment_id == yt_comment_id,
            )
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    assert row.author == "user1"
    assert row.text == "Great video!"
    assert row.like_count == 10

    # Second insert with same yt_comment_id but updated fields
    updated_comments = [
        {
            "yt_comment_id": yt_comment_id,
            "author": "user2",
            "text": "Updated comment text",
            "published_at": datetime.utcnow(),
            "like_count": 42,
        }
    ]
    await dedupe.upsert_comments(db_session, org_id, video_id, updated_comments)

    row = (
        await db_session.execute(
            select(Comment).where(
                Comment.org_id == org_id,
                Comment.video_id == video_id,
                Comment.yt_comment_id == yt_comment_id,
            )
            # ⚠️ Important:
            # SQLAlchemy caches ORM objects inside the session (identity map).
            # Without this option, `scalar_one()` may return a stale in-memory row
            # even after an UPSERT. `populate_existing=True` forces the ORM to
            # overwrite any cached instance with the fresh data returned by the DB.
            # This ensures our test assertions reflect the real persisted state.
            .execution_options(populate_existing=True)
        )
    ).scalar_one()

    # Assert: record updated in place
    assert row.author == "user2"
    assert row.text == "Updated comment text"
    assert row.like_count == 42
