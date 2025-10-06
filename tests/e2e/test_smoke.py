"""
File: test_smoke.py
Layer: E2E
------------
End-to-end smoke test for the YouTube Sentiment Analyzer.

Covers:
    - POST /auth/signup → create org + admin user
    - POST /auth/login → issue JWT
    - POST /ingest/?video_id=... → enqueue ingestion task
    - Internal _fetch_comments() → simulate Celery ingestion worker
    - GET /analytics/distribution?video_id=... → confirm analytics endpoint works

Purpose:
    Happy-path check that the whole system (auth → ingest → analytics) wires together
    under realistic conditions. The ingestion worker is invoked directly to simulate
    Celery execution during tests without mocking or eager mode.
"""

import uuid
import jwt
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.tasks.fetch import _fetch_comments
from app.core.config import settings


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_smoke_signup_login_ingest():
    """
    E2E smoke test:
        - Sign up a new org/user (unique per run)
        - Log in to obtain JWT
        - Ingest a video (enqueue Celery task)
        - Run _fetch_comments manually to simulate worker
        - Fetch analytics distribution for that video
    """
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Signup with unique org/user
        unique = uuid.uuid4().hex[:6]
        signup_payload = {
            "org_name": f"E2EOrg_{unique}",
            "email": f"e2e_{unique}@example.com",
            "password": "password123",
        }
        resp = await client.post("/auth/signup", json=signup_payload)
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]

        # 2. Login
        resp = await client.post(
            "/auth/login",
            json={
                "email": signup_payload["email"],
                "password": signup_payload["password"],
            },
        )
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Ingest a video (enqueue Celery task)
        resp = await client.post(
            "/ingest/",
            params={"video_id": "abc123"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        task_id = resp.json()["task_id"]
        assert task_id

        # 3b. Simulate Celery worker execution (invoke real ingestion coroutine)
        claims = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        org_id = claims["org_id"]
        await _fetch_comments("abc123", org_id)

        # 4. Fetch analytics distribution
        resp = await client.get(
            "/analytics/distribution",
            params={"video_id": "abc123"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

        # 5. Validate response shape
        data = resp.json()
        assert "pos_pct" in data
        assert "neg_pct" in data
        assert "neu_pct" in data
        assert "count" in data
