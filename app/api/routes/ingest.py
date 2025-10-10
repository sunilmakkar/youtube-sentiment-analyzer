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
from app.schemas.ingest import IngestResponse, TaskStatusResponse
from app.services.rate_limiter import check_rate_limit
from app.tasks.celery_app import celery_app
from app.tasks.fetch import fetch_comments_task

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post(
    "/",
    response_model=IngestResponse,
    summary="Ingest YouTube comments",
    description=(
        "Triggers an asynchronous Celery task that fetches YouTube comments for "
        "the given `video_id` and stores them in the database. "
        "Returns a unique task ID for tracking progress."
    ),
)
async def ingest_video(
    video_id: str = Query(..., description="YouTube video_id to ingest"),
    current_user: CurrentUser = Depends(get_current_user),
):
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


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get ingestion task status",
    description=(
        "Returns the Celery task status (PENDING, SUCCESS, FAILURE) "
        "and its result if available. Used by clients to monitor ingestion progress."
    ),
)
async def get_task_status(task_id: str):
    res = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": res.status, "result": res.result}
