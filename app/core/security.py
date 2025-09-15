"""
File: security.py
Purpose:
    Provides security utilities for authentication and authorization.

Key responsibilities:
    - Password hashing and verification with bcrypt.
    - JWT access token creation and decoding.
    - Centralized cryptographic logic used across the app.

Related modules:
    - passlib.context.CryptContext → password hashing (bcrypt).
    - jwt (PyJWT) → encode/decode JWT tokens.
    - app.core.config → provides JWT secret, algorithm, and expiry settings.
"""


from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        password (str): Plaintext password.

    Returns:
        str: Securely hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against its hashed version.

    Args:
        plain (str): Plaintext password.
        hashed (str): Hashed password from DB.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data (dict): Claims to encode in the token (e.g., user_id, org_id, role).
        expires_minutes (int, optional): Expiry in minutes. Defaults to settings.JWT_EXP_MINUTES.

    Returns:
        str: Encoded JWT token string.
    """

    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.JWT_EXP_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token (str): Encoded JWT token string.

    Returns:
        dict: Decoded payload containing claims.
    """
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
