"""
File: deps.py
Purpose:
    Shared FastAPI dependencies for authentication and database access.

Key responsibilities:
    - Define `get_current_user`, a reusable dependency to enforce JWT validation.
    - Ensure only valid, active users (scoped by org_id + role) access protected routes.
    - Decode JWT tokens and map them into a strongly typed `CurrentUser` context object.

Related modules:
    - app/core/security.py → handles JWT encode/decode and password utilities.
    - app/db/session.py → provides async DB sessions.
    - app/models/user.py → User ORM model queried here.
    - app/schemas/auth.py → TokenPayload (JWT claims) and CurrentUser schema.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core import security
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import CurrentUser, TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """
    Dependency: Authenticate and return the current user context.

    Workflow:
        1. Extract JWT token from the request header.
        2. Decode and validate the token payload.
        3. Query the database to confirm the user exists.
        4. Merge DB user data with org_id + role from the token payload.

    Args:
        token (str): JWT access token, injected by FastAPI's `OAuth2PasswordBearer`.
        db (AsyncSession): Async SQLAlchemy session for DB queries.

    Returns:
        CurrentUser: Strongly typed object with `id`, `email`, `org_id`, and `role`.

    Raises:
        HTTPException 401:
            - If token is invalid or expired.
            - If user is not found in the database.
    """
    try:
        payload = security.decode_token(token)
        data = TokenPayload(**payload)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    res = await db.execute(select(User).where(User.id == data.sub))
    db_user = res.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")

    # return merged user + org context
    return CurrentUser(
        id=db_user.id,
        email=db_user.email,
        org_id=data.org_id,
        role=data.role,
    )
