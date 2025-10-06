"""
File: ingest.py
Purpose:
    Handle ingestion of YouTube video comments into the system using Celery.

Key responsibilities:
    - Kick off asynchronous Celery tasks to fetch comments by video_id.
    - Expose task status endpoint so clients can track progress.
    - Enforce multi-tenant isolation (org_id from JWT).

Related modules:
    - app/core/deps.py → provides get_current_user dependency.
    - app/schemas/auth.py → CurrentUser schema for dependency injection.
    - app/tasks/fetch.py → Celery task for fetching comments.
    - app/tasks/celery_app.py → Celery app instance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import get_current_user
from app.schemas.auth import CurrentUser
from app.services.rate_limiter import check_rate_limit
from app.tasks.celery_app import celery_app
from app.tasks.fetch import fetch_comments_task

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
async def ingest_video(
    video_id: str = Query(..., description="YouTube video_id"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Ingest YouTube comments for a given video.

    Steps:
        1. Check per-org rate limit (token bucket in Redis).
        2. If allowed, enqueue Celery task to fetch and persist comments.
        3. Return task_id so client can track status.
        4. If limit exceeded, return 429 Too Many Requests.

    Args:
        video_id (str): YouTube video ID to ingest.
        current_user (CurrentUser): User/org context from JWT.

    Returns:
        dict: JSON with Celery task ID.
            Example:
            {"task_id": "e8d9a83f-3b2c-4c3c-b8d7-5f4a5bbdfe1a"}
    """
    # Rate limit check (per-org)
    allowed = await check_rate_limit(current_user.org_id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
        )

    # Enqueue Celery task
    task = fetch_comments_task.delay(video_id, current_user.org_id)
    return {"task_id": task.id}


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get status of an ingestion task.

    Uses Celery AsyncResult to report status and result
    of a previously submitted ingestion task.

    Args:
        task_id (str): Celery task ID.

    Returns:
        dict: JSON with task ID, status, and result.
            Example:
            {
                "task_id": "e8d9a83f-3b2c-4c3c-b8d7-5f4a5bbdfe1a",
                "status": "SUCCESS",
                "result": {"video_id": "abc123", "comments_fetched": 42}
            }
    """
    res = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": res.status, "result": res.result}
