from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.schemas.auth import CurrentUser
from app.tasks.celery_app import celery_app
from app.tasks.fetch import fetch_comments_task

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
async def ingest_video(
    video_id: str = Query(..., description="YouTube video_id"),
    current_user: CurrentUser = Depends(get_current_user),
):
    task = fetch_comments_task.delay(video_id, current_user.org_id)
    return {"task_id": task.id}


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    res = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": res.status, "result": res.result}
