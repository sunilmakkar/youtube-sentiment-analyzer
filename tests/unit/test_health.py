"""
Unit Test: Health Check Endpoint
--------------------------------
This test verifies that the `/healthz` endpoint is available and returns
an HTTP 200 response in a minimal application context.

Scope:
    - Confirms endpoint responds without errors.
    - Ensures high-level "status" field equals "ok".
    - Allows additional "checks" keys (db, celery, etc.) without failing.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_healthz():
    """
    Verify `/healthz` endpoint returns a 200 OK response
    with at least {"status": "ok"}.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
    data = resp.json()

    # Core assertions
    assert resp.status_code == 200
    assert data["status"] == "ok"

    # Optional deeper checks
    if "checks" in data:
        assert "db" in data["checks"]
        assert "celery" in data["checks"]