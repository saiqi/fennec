from typing import AsyncGenerator, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from fennec_auth.config import settings
from fennec_auth.database import SessionLocal
from fennec_auth.schemas import TokenData
from fennec_auth.models import User, ClientApplication
from fennec_auth.services import (
    get_client_application_by_name,
    get_user_by_user_name,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_current_client_data(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.CLIENT_NAME,
        )
        client_name: str | None = payload.get("sub")
        if not client_name:
            raise credentials_exception
        client_type: str | None = payload.get("client_type")
        if not client_type:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return TokenData(sub=client_name, client_type=client_type)


async def get_current_client(
    session: Annotated[AsyncSession, Depends(get_session)],
    token_data: Annotated[TokenData, Depends(get_current_client_data)],
) -> User | ClientApplication:
    if token_data.client_type == "user":
        current_user = await get_user_by_user_name(session, user_name=token_data.sub)
        if current_user:
            return current_user
    else:
        current_client = await get_client_application_by_name(
            session, name=token_data.sub
        )
        if current_client:
            return current_client
    raise credentials_exception


async def get_current_active_client(
    current_client: Annotated[User | ClientApplication, Depends(get_current_client)],
) -> User | ClientApplication:
    if not current_client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Client is not active"
        )
    return current_client


async def get_current_internal_client(
    current_client: Annotated[
        User | ClientApplication, Depends(get_current_active_client)
    ],
) -> User | ClientApplication:
    if current_client.is_external:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Client is external"
        )
    return current_client
