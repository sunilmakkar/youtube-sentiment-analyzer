"""
File: auth.py
Purpose:
    Handle user authentication and organization-aware signups/logins.

Key responsibilities:
    - Provide endpoints for user signup and login.
    - Issue JWT tokens scoped to user, org, and role.
    - Enforce multi-tenant isolation through JWT claims.
    - Expose a protected /me route for authenticated requests.

Related modules:
    - app/core/security.py → password hashing & JWT utilities.
    - app/core/deps.py → provides get_current_user dependency.
    - app/db/session.py → database session factory.
    - app/models/{user, org, membership}.py → ORM models.
    - app/schemas/auth.py → request/response schemas.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import security
from app.core.deps import get_current_user
from app.db.session import get_session
from app.models import membership, org, user
from app.schemas import auth as schemas

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.TokenResponse)
async def signup(
    payload: schemas.SignupRequest, db: AsyncSession = Depends(get_session)
):
    """
    Sign up a new organization + admin user.

    Steps:
        - Ensure email is not already registered.
        - Create a new Org, User, and Membership (role = admin).
        - Commit all to DB in one transaction.
        - Return a JWT token scoped to org_id and role.

    Args:
        payload (SignupRequest): Org name, email, password.
        db (AsyncSession): Database session (dependency).

    Returns:
        TokenResponse: JWT access token for the new user/org.
    """
    # ensure email not taken
    res = await db.execute(select(user.User).where(user.User.email == payload.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_org = org.Org(id=str(uuid.uuid4()), name=payload.org_name)
    new_user = user.User(
        id=str(uuid.uuid4()),
        email=payload.email,
        hashed_password=security.hash_password(payload.password),
    )
    new_membership = membership.Membership(
        user=new_user, org=new_org, role=membership.RoleEnum.admin
    )
    db.add_all([new_org, new_user, new_membership])
    await db.commit()
    token = security.create_access_token(
        {"sub": new_user.id, "org_id": new_org.id, "role": new_membership.role}
    )
    return schemas.TokenResponse(access_token=token)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(payload: schemas.LoginRequest, db: AsyncSession = Depends(get_session)):
    """
    Authenticate a user and return a JWT token.

    Steps:
        - Look up user by email.
        - Verify password.
        - Fetch first membership (org_id, role).
        - Issue JWT token scoped to that org and role.

    Args:
        payload (LoginRequest): Email + password.
        db (AsyncSession): Database session.

    Returns:
        TokenResponse: JWT access token.
    """
    res = await db.execute(select(user.User).where(user.User.email == payload.email))
    db_user = res.scalar_one_or_none()
    if not db_user or not security.verify_password(
        payload.password, db_user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # pick org + role from membership (first one)
    res = await db.execute(
        select(membership.Membership).where(membership.Membership.user_id == db_user.id)
    )
    m = res.scalar_one()
    token = security.create_access_token(
        {"sub": db_user.id, "org_id": m.org_id, "role": m.role}
    )
    return schemas.TokenResponse(access_token=token)


# --------------------------------------------------
# DUMMY PROTECED ROUTE
# --------------------------------------------------
@router.get("/me")
async def read_users_me(current_user: user.User = Depends(get_current_user)):
    """
    Protected route that returns current user info.

    Args:
        current_user (User): Resolved via JWT in get_current_user.

    Returns:
        dict: Current user's id and email.
    """
    return {"id": current_user.id, "email": current_user.email}
