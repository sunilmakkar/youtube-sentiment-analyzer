"""
Integration Test: Ingest Endpoint
---------------------------------
This test validates the ingestion flow for YouTube comments.

Coverage:
    - POST /ingest → triggers background Celery task.
    - GET /ingest/status/{task_id} → verifies task status API.

Key points:
    - Confirms task_id is returned and non-empty.
    - Ensures status endpoint responds with expected fields.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ingest_and_status_flow(async_client: AsyncClient, auth_headers):
    """
    End-to-end ingestion flow:
        1. Trigger ingestion for a dummy YouTube video_id.
        2. Verify response contains a valid task_id.
        3. Poll the status endpoint and confirm "status" key exists.
    """
    resp = await async_client.post("/ingest/?video_id=abc123", headers=auth_headers["headers"])
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    assert task_id

    status = await async_client.get(f"/ingest/status/{task_id}")
    assert status.status_code == 200
    body = status.json()
    assert "status" in body
