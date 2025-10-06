"""
File: auth.py
Purpose:
    Define Pydantic schemas for authentication and authorization flows.

Key responsibilities:
    - Enforce validation for signup and login requests.
    - Represent JWT tokens, their payload, and the authenticated user context.
    - Provide strongly typed objects shared between routes and services.

Related modules:
    - app/api/routes/auth.py → uses these schemas for request/response models.
    - app/core/security.py → issues/validates JWT tokens.
    - app/core/deps.py → injects CurrentUser from decoded JWT.
"""

from pydantic import BaseModel, EmailStr

from app.models.membership import RoleEnum


class SignupRequest(BaseModel):
    """Request schema for user/org signup."""

    org_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for returning a JWT access token."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Internal schema for JWT payload.

    Attributes:
        sub (str): User ID.
        org_id (str): Organization ID (tenant scoping).
        role (RoleEnum): User's role within the org.
        exp (int): Expiration timestamp (epoch).
    """

    sub: str
    org_id: str
    role: RoleEnum
    exp: int


class CurrentUser(BaseModel):
    """
    Schema representing the authenticated user context.

    Returned by dependencies to unify User + Org context for routes.
    """

    id: str
    email: EmailStr
    org_id: str
    role: RoleEnum
