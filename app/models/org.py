import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.db.base import Base


class Org(Base):
    __tablename__ = "orgs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
