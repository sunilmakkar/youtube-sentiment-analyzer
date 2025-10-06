"""
File: comment_sentiment.py
Purpose:
    Define the CommentSentiment model for persisting results of NLP sentiment analysis
    on YouTube comments.

Key responsibilities:
    - Store sentiment analysis results (label, confidence score, model name).
    - Ensure tenant scoping with org_id for multi-tenancy.
    - Enforce one sentiment record per (org_id, comment_id) via uniqueness constraint.
    - Track when analysis was performed (`analyzed_at`).

Related modules:
    - app/models/comment.py → source comments being analyzed.
    - app/services/nlp_sentiment.py → HuggingFace pipeline running inference.
    - app/tasks/analyze.py → Celery task that populates this table.
"""

import datetime
import uuid

from sqlalchemy import (Column, DateTime, Float, ForeignKey, String,
                        UniqueConstraint)

from app.db.base import Base


class CommentSentiment(Base):
    """
    ORM model mapping for the `comment_sentiment` table.

    Attributes:
        id (str): Primary key (UUID string).
        org_id (str): Foreign key → orgs.id, for tenant scoping.
        comment_id (str): Foreign key → comments.id, links back to original comment.
        label (str): Sentiment classification (e.g., "POSITIVE", "NEGATIVE", "NEUTRAL").
        score (float): Confidence score for the prediction (0.0–1.0).
        model_name (str): Name of the model that generated the sentiment.
        analyzed_at (datetime): Timestamp when the analysis was performed.
    """

    __tablename__ = "comment_sentiment"

    # Primary key (UUID string for consistency with Comment model)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Tenant scoping
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)

    # Reference back to comment
    comment_id = Column(
        String, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )

    # Sentiment analysis fields
    label = Column(String, nullable=False)  # pos | neg | neu
    score = Column(Float, nullable=False)  # confidence score
    model_name = Column(
        String, nullable=False
    )  # e.g. "distilbert-base-uncased-finetuned-sst-2-english"
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Enforce one sentiment per comment per org
    __table_args__ = (
        UniqueConstraint("org_id", "comment_id", name="uq_org_comment_sentiment"),
    )
