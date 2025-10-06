"""
File: user.py
Purpose:
    Define the User model for authentication and account identity.

Key responsibilities:
    - Represent a platform user with login credentials.
    - Securely store passwords (hashed, never plain).
    - Provide base identity for role-based access via memberships.

Related modules:
    - app/core/security.py → handles password hashing + JWTs.
    - app/models/membership.py → links users to organizations with roles.
    - app/api/routes/auth.py → signup/login endpoints interact with this model.

Schema:
    users
    ┌────────────┬────────────────────┬─────────────────┬─────────────┐
    │ id (PK)    │ email (unique, ix) │ hashed_password │ created_at  │
    └────────────┴────────────────────┴─────────────────┴─────────────┘
"""

import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    """
    ORM model mapping for the `users` table.

    Attributes:
        id (str): Primary key (UUID string).
        email (str): User email (unique, indexed).
        hashed_password (str): Secure password hash.
        created_at (datetime): Timestamp when the user was created.
    """

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
