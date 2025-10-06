"""
File: test_auth.py
Layer: Integration
------------------
Integration tests for authentication endpoints.

Targets:
    - POST /auth/signup
    - POST /auth/login
    - GET /auth/me

Key aspects validated:
    - New org + admin user can be created via signup.
    - Valid login issues a JWT token.
    - Invalid login rejects credentials.
    - Protected `/auth/me` route requires Authorization header.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_creates_org_and_user(async_client: AsyncClient):
    """
    Verify that `/auth/signup` creates a new org + admin user
    and returns a valid JWT token.
    """
    payload = {
        "org_name": "AuthTestOrg",
        "email": "authuser@example.com",
        "password": "secret123",
    }
    resp = await async_client.post("/auth/signup", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_returns_token(async_client: AsyncClient):
    """
    Verify that `/auth/login` accepts valid credentials
    and returns a JWT token.
    """
    payload = {"email": "authuser@example.com", "password": "secret123"}
    resp = await async_client.post("/auth/login", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"]


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(async_client: AsyncClient):
    """
    Verify that `/auth/login` rejects invalid credentials.
    """
    payload = {"email": "authuser@example.com", "password": "wrongpass"}
    resp = await async_client.post("/auth/login", json=payload)

    assert resp.status_code == 401
    data = resp.json()
    assert data["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_me_requires_auth(async_client: AsyncClient):
    """
    Verify that `/auth/me` requires Authorization header.
    """
    resp = await async_client.get("/auth/me")

    assert resp.status_code == 401
    data = resp.json()
    assert data["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_me_returns_current_user(async_client: AsyncClient):
    """
    Verify that `/auth/me` returns current user info
    when called with a valid token.
    """
    # First login to get token
    login_payload = {"email": "authuser@example.com", "password": "secret123"}
    resp = await async_client.post("/auth/login", json=login_payload)
    token = resp.json()["access_token"]

    # Call /me with Authorization header
    resp = await async_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data and "email" in data
    assert data["email"] == "authuser@example.com"
