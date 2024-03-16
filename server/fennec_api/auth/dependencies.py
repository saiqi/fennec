from typing import Annotated
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_api.core.config import settings
from fennec_api.core.dependencies import get_session
from fennec_api.auth.schemas import TokenData
from fennec_api.users.models import User
from fennec_api.users.schemas import Role
import fennec_api.users.service as user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user_data(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str | None = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return TokenData(email=email)


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    token_data: Annotated[TokenData, Depends(get_current_user_data)],
) -> User:
    user = await user_service.get_user_by_email(session, email=token_data.email)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incative user"
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if current_user.role != Role.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficent priviledge"
        )
    return current_user
