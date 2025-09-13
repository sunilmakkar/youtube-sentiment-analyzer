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
