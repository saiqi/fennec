import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import fennec_api.users.service as user_service
from fennec_api.users.models import User
from fennec_api.users.schemas import (
    UserCreate,
    Role,
    UserUpdateRole,
    UserUpdatePassword,
    UserUpdateStatus,
)
from fennec_api.users.exceptions import AlreadyRegisteredUser


@pytest.mark.asyncio
async def test_create_and_authenticate_user(session: AsyncSession) -> None:
    await user_service.create_user(
        session,
        obj_in=UserCreate(email="rino.dellanegra@redstarfc.fr", password="password"),
    )
    user = await user_service.authenticate_user(
        session, email="rino.dellanegra@redstarfc.fr", password="password"
    )
    assert user
    assert user.role == "read"
    assert not user.disabled
    assert user.created_at == user.updated_at


@pytest.mark.asyncio
async def test_create_existing_user(session: AsyncSession, existing_user: User) -> None:
    with pytest.raises(AlreadyRegisteredUser):
        await user_service.create_user(
            session, obj_in=UserCreate(email=existing_user.email, password="password")
        )


@pytest.mark.asyncio
async def test_update_user_password(session: AsyncSession, existing_user: User) -> None:
    await user_service.update_user_password(
        session, id=existing_user.id, obj_in=UserUpdatePassword(password="new-password")
    )
    updated_user = await user_service.authenticate_user(
        session, email=existing_user.email, password="new-password"
    )
    assert updated_user
    assert updated_user.role == "read"
    assert not updated_user.disabled


@pytest.mark.asyncio
async def test_disable_user(session: AsyncSession, existing_user: User) -> None:
    await user_service.update_user_status(
        session, id=existing_user.id, obj_in=UserUpdateStatus(disabled=True)
    )
    updated_user = await user_service.authenticate_user(
        session, email=existing_user.email, password="password"
    )
    assert updated_user
    assert updated_user.disabled
    assert updated_user.role == "read"


@pytest.mark.asyncio
async def test_update_user_role(session: AsyncSession, existing_user: User) -> None:
    await user_service.update_user_role(
        session, id=existing_user.id, obj_in=UserUpdateRole(role=Role.ADMIN)
    )
    updated_user = await user_service.authenticate_user(
        session, email=existing_user.email, password="password"
    )
    assert updated_user
    assert updated_user.role == "admin"
    assert not updated_user.disabled


@pytest.mark.asyncio
async def test_list_users(session: AsyncSession, existing_user: User) -> None:
    users = await user_service.list_users(session)
    assert users
    assert len(list(users)) == 1
