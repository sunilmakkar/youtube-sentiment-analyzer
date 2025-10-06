"""
Shared pytest fixtures for integration + unit tests.

Provides:
    - async_client: httpx.AsyncClient bound to FastAPI app.
    - auth_headers: provisions a fresh Org+User and returns a valid JWT.
    - current_user: fake authenticated user bound to the test org.
    - seeded_comments_for_auth: seed one video + comments under JWT org_id.
    - seeded_sentiments_for_auth: extends seeded_comments_for_auth with sentiments.
    - db_session: yields a fresh SQLAlchemy AsyncSession per test (truncated tables).
    - redis_client: isolated Redis client per test.
    - mock_celery: mock Celery tasks for ingestion/status flow.
"""

import uuid
import pytest
import pytest_asyncio
import redis.asyncio as aioredis
import asyncio

from httpx import ASGITransport, AsyncClient
from datetime import datetime
from sqlalchemy import select, text

from app.db.session import async_session
from app.main import app
from app.models import Comment, CommentSentiment, Video
from app.schemas.auth import CurrentUser
from app.core.config import settings

# ==============================================================================
# Event Loop
# ==============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """Single event loop for all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==============================================================================
# Async HTTP Client
# ==============================================================================
@pytest_asyncio.fixture
async def async_client():
    """httpx.AsyncClient bound to FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ==============================================================================
# Authorization Header (fresh Org + User each test)
# ==============================================================================
@pytest_asyncio.fixture
async def auth_headers(async_client, db_session):
    """
    Fixture: Provisions a fresh org+user via /auth/signup after DB reset,
    logs in, and returns both the JWT header and org_id.
    """
    import base64, json, uuid

    unique_suffix = str(uuid.uuid4())[:8]
    email = f"user_{unique_suffix}@example.com"
    password = "secret123"
    org_name = f"Org_{unique_suffix}"

    # Signup
    resp = await async_client.post(
        "/auth/signup", json={"org_name": org_name, "email": email, "password": password}
    )
    assert resp.status_code in (200, 201), f"Signup failed: {resp.text}"

    token = resp.json()["access_token"]
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "===").decode())
    org_id = claims["org_id"]

    # Login
    resp = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]

    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "org_id": org_id,
    }


# ==============================================================================
# Current User (synthetic, for unit tests)
# ==============================================================================
@pytest.fixture
def current_user(auth_headers):
    """Fake authenticated user for unit tests."""
    return CurrentUser(
        id=str(uuid.uuid4()),
        email="test@example.com",
        org_id=auth_headers["org_id"],
        role="admin",
    )


# ==============================================================================
# Seeded Comments (Video + Comments under JWT org_id)
# ==============================================================================
@pytest_asyncio.fixture
async def seeded_comments_for_auth(db_session, auth_headers):
    """Seed one video + comments tied to the JWT org_id."""
    org_id = auth_headers["org_id"]

    video = Video(
        id=str(uuid.uuid4()),
        org_id=org_id,
        yt_video_id="abc123",
        title="Test Video",
        channel_id="test_channel",
        fetched_at=datetime.utcnow(),
    )
    db_session.add(video)
    await db_session.flush()

    comments = [
        Comment(
            id=str(uuid.uuid4()),
            org_id=org_id,
            video_id=video.id,
            yt_comment_id="c1",
            author="user1",
            text="I love this video!",
            published_at=datetime.utcnow(),
            like_count=5,
        ),
        Comment(
            id=str(uuid.uuid4()),
            org_id=org_id,
            video_id=video.id,
            yt_comment_id="c2",
            author="user2",
            text="This is terrible",
            published_at=datetime.utcnow(),
            like_count=2,
        ),
    ]
    db_session.add_all(comments)
    await db_session.commit()
    return video


# ==============================================================================
# Seeded Sentiments (extends Seeded Comments)
# ==============================================================================
@pytest_asyncio.fixture
async def seeded_sentiments_for_auth(seeded_comments_for_auth, db_session, auth_headers):
    """Attach sentiments to seeded comments under JWT org_id."""
    org_id = auth_headers["org_id"]

    comments = (
        await db_session.execute(
            select(Comment).where(Comment.video_id == seeded_comments_for_auth.id)
        )
    ).scalars().all()

    for comment, (label, score) in zip(comments, [("pos", 0.95), ("neg", 0.90)]):
        sentiment = CommentSentiment(
            id=str(uuid.uuid4()),
            org_id=org_id,
            comment_id=comment.id,
            label=label,
            score=score,
            model_name="test-model",
            analyzed_at=datetime.utcnow(),
        )
        db_session.add(sentiment)

    await db_session.commit()
    return seeded_comments_for_auth


# ==============================================================================
# Database Session (truncate between tests, keep orgs)
# ==============================================================================
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Fixture: Yields a fresh database session for each test.
    Ensures clean slate by truncating relevant tables, including users/orgs.
    """
    async with async_session() as session:
        for table in [
            "sentiment_aggregates",
            "comment_sentiment",
            "comments",
            "videos",
            "users",
            "orgs",
        ]:
            await session.execute(text(f"TRUNCATE {table} CASCADE"))
        await session.commit()
        yield session


# ==============================================================================
# Redis Client
# ==============================================================================
@pytest_asyncio.fixture(scope="function")
async def redis_client():
    """Isolated Redis client per test."""
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.close()


# ==============================================================================
# Patch Rate Limiter Redis
# ==============================================================================
@pytest_asyncio.fixture(autouse=True)
async def _patch_rate_limiter_redis(redis_client):
    """Patch rate_limiter to use test Redis client."""
    from app.services import rate_limiter
    rate_limiter.redis = redis_client
    yield


"""
File: security.py
Purpose:
    Provides security utilities for authentication and authorization.

Key responsibilities:
    - Password hashing and verification with bcrypt.
    - JWT access token creation and decoding.
    - Centralized cryptographic logic used across the app.

Related modules:
    - passlib.context.CryptContext → password hashing (bcrypt).
    - jwt (PyJWT) → encode/decode JWT tokens.
    - app.core.config → provides JWT secret, algorithm, and expiry settings.
"""

from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password (str): Plaintext password.

    Returns:
        str: Securely hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against its hashed version.

    Args:
        plain (str): Plaintext password.
        hashed (str): Hashed password from DB.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data (dict): Claims to encode in the token (e.g., user_id, org_id, role).
        expires_minutes (int, optional): Expiry in minutes. Defaults to settings.JWT_EXP_MINUTES.

    Returns:
        str: Encoded JWT token string.
    """

    to_encode = data.copy()

    # Use default only if expires_minutes is not provided
    if expires_minutes is None:
        expires_minutes = settings.JWT_EXP_MINUTES

    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token (str): Encoded JWT token string.

    Returns:
        dict: Decoded payload containing claims.
    """
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )

