"""
Unit Test: Readiness Check Endpoint
-----------------------------------
This test verifies that the `/readyz` endpoint is available and returns
an HTTP 200 response with dependency health information.

Scope:
    - Confirms endpoint responds without errors.
    - Ensures top-level "status" field exists.
    - Validates presence of dependency check keys (db, redis, celery, hf_model).
    - Does not require actual dependencies to be healthy:
        accepts "ok", "error", or "not_loaded".
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_readyz_endpoint():
    """
    Verify `/readyz` endpoint returns a 200 OK response
    and includes all expected dependency checks.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/readyz")
    data = resp.json()

    # Core assertions
    assert resp.status_code == 200
    assert "status" in data
    assert "checks" in data

    # Dependency checks should always include these keys
    checks = data["checks"]
    for dep in ["db", "redis", "celery", "hf_model"]:
        assert dep in checks
        assert "status" in checks[dep]

    # hf_model should always include a loaded flag
    assert "loaded" in checks["hf_model"]
