from typing import Any, Iterable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from fennec_api.users.models import User
from fennec_api.users.schemas import (
    UserCreate,
    Role,
    UserUpdatePassword,
    UserUpdateRole,
    UserUpdateStatus,
)
from fennec_api.users.exceptions import AlreadyRegisteredUser
from fennec_api.core.security import get_password_hash, verify_password


async def get_user_by_email(session: AsyncSession, *, email: str) -> User | None:
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def list_users(session: AsyncSession) -> Iterable[User]:
    result = await session.execute(select(User).order_by(User.id))
    return result.scalars()


async def create_user(session: AsyncSession, *, obj_in: UserCreate) -> User:
    db_obj = User(
        email=obj_in.email,
        hashed_password=get_password_hash(obj_in.password),
        disabled=False,
        role=Role.READ.value,
    )
    session.add(db_obj)
    try:
        await session.commit()
    except IntegrityError:
        raise AlreadyRegisteredUser(f"{obj_in.email} already exists")
    await session.refresh(db_obj)
    return db_obj


async def authenticate_user(
    session: AsyncSession, *, email: str, password: str
) -> User | None:
    user = await get_user_by_email(session, email=email)
    if not user:
        return None
    if not verify_password(
        plain_password=password, hashed_password=user.hashed_password
    ):
        return None
    return user


async def update_user(
    session: AsyncSession, *, id: int, updates: dict[str, Any]
) -> None:
    await session.execute(update(User).where(User.id == id).values(updates))
    await session.commit()


async def update_user_password(
    session: AsyncSession, *, id: int, obj_in: UserUpdatePassword
) -> None:
    await update_user(
        session, id=id, updates={"hashed_password": get_password_hash(obj_in.password)}
    )


async def update_user_status(
    session: AsyncSession, *, id: int, obj_in: UserUpdateStatus
) -> None:
    await update_user(session, id=id, updates={"disabled": obj_in.disabled})


async def update_user_role(
    session: AsyncSession, *, id: int, obj_in: UserUpdateRole
) -> None:
    await update_user(session, id=id, updates={"role": obj_in.role.value})
