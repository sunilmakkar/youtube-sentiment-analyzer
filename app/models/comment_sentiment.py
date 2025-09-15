from sqlalchemy import Column, String, Float, DateTime, ForeignKey, UniqueConstraint
import datetime
import uuid

from app.db.base import Base

class CommentSentiment(Base):
    __tablename__ = "comment_sentiment"

    # Primary key (UUID string for consistency with Comment model)
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Tenant scoping
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)

    # Reference back to comment
    comment_id = Column(String, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)

    # Sentiment analysis fields
    label = Column(String, nullable=False) # pos | neg | neu
    score = Column(Float, nullable=False) # confidence score
    model_name = Column(String, nullable=False) # e.g. "distilbert-base-uncased-finetuned-sst-2-english"
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Enforce one sentiment per comment per org
    __table_args__ = (UniqueConstraint("org_id", "comment_id", name="uq_org_comment_sentiment"),)