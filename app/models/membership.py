"""
File: membership.py
Purpose:
    Define the Membership model, linking users to organizations with roles.

Key responsibilities:
    - Represent many-to-many relationship between users and orgs.
    - Enforce one role per (user_id, org_id).
    - Allow role-based authorization (admin vs. member).
    - Provide bidirectional relationships for ORM navigation.

Related modules:
    - app/models/user.py → users table (accounts).
    - app/models/org.py → organizations table (tenants).
    - app/api/routes/auth.py → uses membership to assign roles during signup/login.
"""


import enum

from sqlalchemy import Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class RoleEnum(str, enum.Enum):
    """Role options for a membership: admin or member."""
    admin = "admin"
    member = "member"


class Membership(Base):
    """
    ORM model mapping for the `memberships` table.

    Attributes:
        user_id (str): Foreign key → users.id (part of composite PK).
        org_id (str): Foreign key → orgs.id (part of composite PK).
        role (RoleEnum): Role assigned within this organization.

    Relationships:
        user (User): ORM backref → list of user memberships.
        org (Org): ORM backref → list of org memberships.
    """
    __tablename__ = "memberships"

    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    org_id = Column(String, ForeignKey("orgs.id"), primary_key=True)
    role = Column(Enum(RoleEnum), nullable=False)

    user = relationship("User", backref="memberships")
    org = relationship("Org", backref="memberships")
