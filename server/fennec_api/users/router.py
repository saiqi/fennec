from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_api.auth.dependencies import get_current_active_user, get_current_admin
from fennec_api.core.dependencies import get_session
from fennec_api.users.models import User
from fennec_api.users.schemas import (
    UserOut,
    UserCreate,
    UserUpdatePassword,
    UserUpdateStatus,
    UserUpdateRole,
)
from fennec_api.users.exceptions import AlreadyRegisteredUser
import fennec_api.users.service as user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def register_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_create: Annotated[UserCreate, Body(...)],
) -> Any:
    try:
        user = await user_service.create_user(session, obj_in=user_create)
    except AlreadyRegisteredUser as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.get("", response_model=list[UserOut])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)],
) -> Any:
    return await user_service.list_users(session)


@router.get("/me", response_model=UserOut)
async def read_users_me(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    return current_user


@router.post("/{user_id}/update-password", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_password(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_update: Annotated[UserUpdatePassword, Body(...)],
    user_id: int,
) -> None:
    await user_service.update_user_password(session, id=user_id, obj_in=user_update)


@router.post("/{user_id}/update-status", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_status(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)],
    user_update: Annotated[UserUpdateStatus, Body(...)],
    user_id: int,
) -> None:
    await user_service.update_user_status(session, id=user_id, obj_in=user_update)


@router.post("/{user_id}/update-role", status_code=status.HTTP_204_NO_CONTENT)
async def update_user_role(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_admin: Annotated[User, Depends(get_current_admin)],
    user_update: Annotated[UserUpdateRole, Body(...)],
    user_id: int,
) -> None:
    await user_service.update_user_role(session, id=user_id, obj_in=user_update)
