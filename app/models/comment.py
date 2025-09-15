from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, UniqueConstraint
import uuid

from app.db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    yt_comment_id = Column(String, nullable=False)
    author = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    like_count = Column(Integer, default=0)
    parent_id = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("org_id", "yt_comment_id", name="uq_org_comment"),)
