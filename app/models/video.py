import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    yt_video_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    channel_id = Column(String, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_analyzed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("org_id", "yt_video_id", name="uq_video_per_org"),
    )
