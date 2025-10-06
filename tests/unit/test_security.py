"""
File: test_security.py
Layer: Unit
------------
Unit tests for the Security utilities.

Targets:
    - hash_password / verify_password
    - create_access_token
    - decode_token

Key aspects validated:
    - Password hashing and verification roundtrip.
    - JWT token creation with expiry claim.
    - Decoding returns expected payload.
    - Expired tokens raise exceptions.
"""


import pytest
import time
import jwt

from app.core import security
from app.core.config import settings


def test_password_hash_and_verify_roundtrip():
    """
    It should hash a password and successfully verify at.
    """
    raw_password = "supersecret123"
    hashed = security.hash_password(raw_password)

    assert hashed != raw_password # hash should not equal plaintext
    assert security.verify_password(raw_password, hashed) is True
    assert security.verify_password("wrongpassword", hashed) is False


def test_create_and_decode_access_token():
    """
    It should create a JWT with claims and decode it back correctly.
    """
    payload = {"sub": "user123", "org_id": "org456", "role": "admin"}
    token = security.create_access_token(payload, expires_minutes=5)

    decoded = security.decode_token(token)
    assert decoded["sub"] == payload["sub"]
    assert decoded["org_id"] == payload["org_id"]
    assert decoded["role"] == payload["role"]
    assert "exp" in decoded


def test_expired_token_raises():
    """
    It should raise when decoding an expired JWT.
    """
    payload = {"sub": "user123", "org_id": "org456", "role": "admin"}
    token = security.create_access_token(payload, expires_minutes=0)

    time.sleep(1)  # ensure token is expired
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_token(token)