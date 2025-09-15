"""
File: org.py
Purpose:
    Define the Org (organization) model for tenant scoping in a multi-tenant system.

Key responsibilities:
    - Represent an organization (tenant) within the platform.
    - Provide isolation for data across multiple orgs (multi-tenancy).
    - Serve as the anchor for memberships, users, videos, and comments.

Related modules:
    - app/models/user.py → users belong to orgs via memberships.
    - app/models/membership.py → join table connecting users and orgs.
    - app/models/video.py → videos are tied to orgs.
    - app/models/comment.py → comments are scoped to orgs.

Schema:
    orgs
    ┌────────────┬───────────────┬─────────────┐
    │ id (PK)    │ name (unique) │ created_at  │
    └────────────┴───────────────┴─────────────┘
"""


import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.db.base import Base


class Org(Base):
    """
    ORM model mapping for the `orgs` table.

    Attributes:
        id (str): Primary key (UUID string).
        name (str): Organization name, unique per tenant.
        created_at (datetime): Timestamp when the org was created.
    """
    __tablename__ = "orgs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
