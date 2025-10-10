"""
File: ingest.py
Layer: Schema
-------------
Pydantic models for the Ingest API.

Defines structured response formats for:
    - /ingest/ → enqueues comment ingestion task.
    - /ingest/status/{task_id} → reports Celery task progress.

Purpose:
    Enables typed, self-documented API responses in Swagger and ReDoc.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class IngestResponse(BaseModel):
    """Response model for POST /ingest/"""
    task_id: str = Field(..., description="Celery task ID tracking ingestion progress")

    class Config:
        json_schema_extra = {
            "example": {"task_id": "e8d9a83f-3b2c-4c3c-b8d7-5f4a5bbdfe1a"}
        }


class TaskStatusResult(BaseModel):
    """Inner model for the `result` object returned by Celery."""
    video_id: Optional[str] = Field(None, description="YouTube video ID that was processed")
    comments_fetched: Optional[int] = Field(None, description="Number of comments fetched")


class TaskStatusResponse(BaseModel):
    """Response model for GET /ingest/status/{task_id}"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Current task state (e.g., PENDING, SUCCESS, FAILURE)")
    result: Optional[TaskStatusResult] = Field(None, description="Detailed result if available")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "e8d9a83f-3b2c-4c3c-b8d7-5f4a5bbdfe1a",
                "status": "SUCCESS",
                "result": {"video_id": "abc123", "comments_fetched": 42}
            }
        }
