import enum

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    member = "member"


class Membership(Base):
    __tablename__ = "memberships"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    org_id = Column(String, ForeignKey("orgs.id"), primary_key=True)
    role = Column(Enum(RoleEnum), nullable=False)

    user = relationship("User", backref="memberships")
    org = relationship("Org", backref="memberships")
