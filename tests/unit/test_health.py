"""
Unit Test: Health Check Endpoint
--------------------------------
This test verifies that the `/healthz` endpoint is available and returns
an HTTP 200 response in a minimal application context.

Scope:
    - Confirms endpoint responds without errors.
    - Ensures high-level "status" field equals "ok".
    - Uses ASGITransport for in-process testing (no real network calls).
"""


import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_healthz():
    """
    Verify `/healthz` endpoint returns a 200 OK response
    and a minimal JSON body with {"status": "ok"}.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}