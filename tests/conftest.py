"""
Shared pytest fixtures for integration + unit tests.

Provides:
    - event_loop: AsyncIO event loop for pytest-asyncio.
    - async_client: httpx.AsyncClient bound to FastAPI app.
    - auth_headers: reusable Authorization header for authenticated requests.
    - current_org: ensure a test Org row exists in the DB.
    - current_user: fake authenticated user bound to the test org.
    - seeded_comments: seed one video + comments + sentiments for analytics tests.
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.schemas.auth import CurrentUser
from app.db.session import async_session
from app.models import Org, Video, Comment, CommentSentiment
from app.main import app


# ==============================================================================
# AsyncIO Event Loop (pytest-asyncio requirement)
# ==============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """
    Provide a session-scoped event loop for pytest-asyncio.
    Ensures async tests and fixtures can run properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==============================================================================
# Async HTTP Client
# ==============================================================================
@pytest_asyncio.fixture
async def async_client():
    """
    Fixture: Async HTTP client bound to FastAPI app.
    Allows calling API routes without running a server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ==============================================================================
# Authorization Header (real login/signup)
# ==============================================================================
@pytest_asyncio.fixture
async def auth_headers(async_client):
    """
    Fixture: Get a real JWT by logging in first, or sign up if necessary.
    Idempotent: ensures we never trigger duplicate Org/User inserts.
    """
    login_payload = {
        "email": "test@example.com",
        "password": "secret123",
    }

    # 1. Try login first
    resp = await async_client.post("/auth/login", json=login_payload)
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # 2. Check if org already exists (avoid duplicate key)
    async with async_session() as session:
        from app.models import Org
        from sqlalchemy import select

        existing = await session.execute(select(Org).where(Org.name == "Test Org"))
        if existing.scalar_one_or_none():
            raise RuntimeError(
                "Test Org already exists but login failed. "
                "Likely due to password mismatch between fixture and DB."
            )

    # 3. Otherwise, create fresh org + user via signup
    signup_payload = {
        "org_name": "Test Org",
        "email": login_payload["email"],
        "password": login_payload["password"],
    }
    resp = await async_client.post("/auth/signup", json=signup_payload)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}




# ==============================================================================
# Current Org (idempotent: get-or-create)
# ==============================================================================
@pytest_asyncio.fixture
async def current_org():
    """
    Fixture: Ensure a test Org row exists in the DB.
    Uses get-or-create logic to avoid duplicate key errors
    when multiple tests reuse the same "Test Org".
    """
    async with async_session() as session:
        existing = await session.execute(
            select(Org).where(Org.name == "Test Org")
        )
        org = existing.scalar_one_or_none()
        if org is None:
            org = Org(
                id=str(uuid.uuid4()),
                name="Test Org",
            )
            session.add(org)
            await session.commit()
        return org


# ==============================================================================
# Current User
# ==============================================================================
@pytest.fixture
def current_user(current_org):
    """
    Fixture: Fake authenticated user bound to the test Org.
    Matches the structure of app.schemas.auth.CurrentUser.
    """
    return CurrentUser(
        id=str(uuid.uuid4()),
        email="test@example.com",
        org_id=current_org.id,  # ✅ ensures DB integrity
        role="admin",
    )


# ==============================================================================
# Seeded Comments (Video + Comments + Sentiments)
# ==============================================================================
@pytest_asyncio.fixture
async def seeded_comments(current_user):
    """
    Fixture: Seed one video, two comments, and their sentiments.
    Provides realistic data for analytics-related tests.

    Idempotent logic:
        - Reuses existing Video if already present.
        - Reuses existing Comments and Sentiments if they exist.
        - Guarantees no duplicate key violations on repeated test runs.
    """
    async with async_session() as session:
        # 1. Get-or-create Video
        existing_video = await session.execute(
            select(Video).where(
                Video.org_id == current_user.org_id,
                Video.yt_video_id == "abc123",
            )
        )
        video = existing_video.scalar_one_or_none()
        if video is None:
            video = Video(
                id=str(uuid.uuid4()),
                org_id=current_user.org_id,
                yt_video_id="abc123",
                title="Test Video",
                channel_id="test_channel",
                fetched_at=datetime.utcnow(),
            )
            session.add(video)
            await session.flush()

        # 2. Get-or-create Comments
        comments = []
        for yt_id, author, text in [
            ("c1", "user1", "I love this video!"),
            ("c2", "user2", "This is terrible"),
        ]:
            existing_comment = await session.execute(
                select(Comment).where(
                    Comment.org_id == current_user.org_id,
                    Comment.video_id == video.id,
                    Comment.yt_comment_id == yt_id,
                )
            )
            comment = existing_comment.scalar_one_or_none()
            if comment is None:
                comment = Comment(
                    id=str(uuid.uuid4()),
                    org_id=current_user.org_id,
                    video_id=video.id,
                    yt_comment_id=yt_id,
                    author=author,
                    text=text,
                    published_at=datetime.utcnow(),
                    like_count=5 if yt_id == "c1" else 2,
                )
                session.add(comment)
                await session.flush()
            comments.append(comment)

        # 3. Get-or-create Sentiments
        for comment, (label, score) in zip(comments, [("pos", 0.95), ("neg", 0.90)]):
            existing_sent = await session.execute(
                select(CommentSentiment).where(
                    CommentSentiment.org_id == current_user.org_id,
                    CommentSentiment.comment_id == comment.id,
                )
            )
            sentiment = existing_sent.scalar_one_or_none()
            if sentiment is None:
                sentiment = CommentSentiment(
                    id=str(uuid.uuid4()),
                    org_id=current_user.org_id,
                    comment_id=comment.id,
                    label=label,
                    score=score,
                    model_name="test-model",
                    analyzed_at=datetime.utcnow(),
                )
                session.add(sentiment)

        # 4. Commit everything
        await session.commit()
        return video
