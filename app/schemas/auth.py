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

    class Config:
        json_schema_extra = {
            "example": {
                "org_name": "Acme Corp",
                "email": "admin@acme.com",
                "password": "password123"
            }
        }


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@acme.com",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """Response schema for returning a JWT access token."""
    access_token: str
    token_type: str = "bearer"

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenPayload(BaseModel):
    """Internal schema for JWT payload."""
    sub: str
    org_id: str
    role: RoleEnum
    exp: int


class CurrentUser(BaseModel):
    """Schema representing the authenticated user context."""
    id: str
    email: EmailStr
    org_id: str
    role: RoleEnum


class UserResponse(BaseModel):
    """Response schema for /auth/me route."""
    id: str
    email: EmailStr
    org_id: str
    role: RoleEnum

    class Config:
        json_schema_extra = {
            "example": {
                "id": "1d2a3f45-678b-49cd-a890-ef1234567890",
                "email": "user@acme.com",
                "org_id": "9c4a7b12-456e-40f9-b8de-11a56b87c123",
                "role": "admin"
            }
        }
