"""
File: keywords.py
Purpose:
    Placeholder for keyword extraction tasks.
    Prevents Celery import errors until the real implementation is added.
"""

from app.tasks.celery_app import celery_app

@celery_app.task(name="task.extract_keywords")
def extract_keywords(video_id: str):
    """
    Temporary no-op task. Real logic will come later.
    """
    return {"video_id": video_id, "keywords": []}
