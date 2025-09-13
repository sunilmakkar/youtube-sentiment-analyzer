import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ingest_and_status_flow(async_client: AsyncClient, auth_headers):
    resp = await async_client.post("/ingest/?video_id=abc123", headers=auth_headers)
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]
    assert task_id

    status = await async_client.get(f"/ingest/status/{task_id}")
    assert status.status_code == 200
    body = status.json()
    assert "status" in body
