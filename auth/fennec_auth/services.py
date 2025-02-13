from typing import Sequence
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_auth.schemas import (
    UserCreate,
    GroupCreate,
    GroupUpdate,
    ClientApplicationCreate,
    ActiveStatusUpdate,
    ExternalStatusUpdate,
    PasswordUpdate,
    PermissionUpdate,
    RoleType,
)
from fennec_auth.models import (
    User,
    Group,
    ClientApplication,
    Permission,
    UserPermission,
    ClientApplicationPermission,
)
from fennec_auth.security import (
    random_password,
    get_password_hash,
    verify_password,
    random_client_id,
    random_client_secret,
)
from fennec_auth.exceptions import (
    AlreadyRegisteredUser,
    AlreadyRegisteredGroup,
    AlreadyRegisteredClientApplication,
    AlreadyAttachedPermission,
    GroupNotFound,
    ClientApplicationNotFound,
)


async def list_groups(session: AsyncSession) -> Sequence[Group]:
    result = await session.execute(select(Group))
    return result.scalars().all()


async def get_group_by_name(session: AsyncSession, name: str) -> Group | None:
    result = await session.execute(select(Group).filter(Group.name == name))
    return result.scalar_one_or_none()


async def create_group(session: AsyncSession, group_data: GroupCreate) -> Group:
    if await get_group_by_name(session, name=group_data.name):
        raise AlreadyRegisteredGroup(f"Group {group_data.name} already exists")
    db_obj = Group(name=group_data.name)
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def list_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def get_user_by_user_name(session: AsyncSession, user_name: str) -> User | None:
    result = await session.execute(select(User).filter(User.user_name == user_name))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    if await get_user_by_user_name(session, user_name=user_data.user_name):
        raise AlreadyRegisteredUser(f"User {user_data.user_name} already exists")

    if await get_user_by_email(session, email=user_data.email):
        raise AlreadyRegisteredUser(f"User with email {user_data.email} already exists")

    password = random_password()
    db_obj = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        user_name=user_data.user_name,
        email=user_data.email,
        role=user_data.role,
        password_hash=get_password_hash(password),
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)

    return db_obj


async def authenticate_user(
    session: AsyncSession, *, user_name: str, password: str
) -> User | None:
    user = await get_user_by_user_name(session, user_name=user_name)
    if not user:
        return None
    if not verify_password(plain_password=password, hashed_password=user.password_hash):
        return None
    return user


async def list_client_applications(
    session: AsyncSession,
) -> Sequence[ClientApplication]:
    result = await session.execute(select(ClientApplication))
    return result.scalars().all()


async def get_client_application_by_name(
    session: AsyncSession, name: str
) -> ClientApplication | None:
    result = await session.execute(
        select(ClientApplication).filter(ClientApplication.name == name)
    )
    return result.scalar_one_or_none()


async def get_client_application_by_client_id(
    session: AsyncSession, client_id: str
) -> ClientApplication | None:
    result = await session.execute(
        select(ClientApplication).filter(ClientApplication.client_id == client_id)
    )
    return result.scalar_one_or_none()


async def create_client_application(
    session: AsyncSession, client_application_data: ClientApplicationCreate
) -> ClientApplication:
    if await get_client_application_by_name(session, name=client_application_data.name):
        raise AlreadyRegisteredClientApplication(
            f"Client application {client_application_data.name} already exists"
        )
    client_id = random_client_id()
    client_secret = random_client_secret()
    db_obj = ClientApplication(
        name=client_application_data.name,
        client_id=client_id,
        client_secret_hash=get_password_hash(client_secret),
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def authenticate_client_application(
    session: AsyncSession, *, client_id: str, client_secret: str
) -> ClientApplication | None:
    client_application = await get_client_application_by_client_id(
        session, client_id=client_id
    )
    if not client_application:
        return None
    if not verify_password(
        plain_password=client_secret,
        hashed_password=client_application.client_secret_hash,
    ):
        return None
    return client_application


async def update_groups(
    session: AsyncSession, model: User | ClientApplication, update_data: GroupUpdate
) -> User | ClientApplication:
    group = await get_group_by_name(session, name=update_data.name)
    if not group:
        raise GroupNotFound(f"Group {update_data.name} not found")
    model.groups = group
    await session.commit()
    await session.refresh(model)
    return model


async def update_active_status(
    session: AsyncSession,
    model: User | ClientApplication,
    update_data: ActiveStatusUpdate,
) -> User | ClientApplication:
    model.is_active = update_data.is_active
    await session.commit()
    await session.refresh(model)
    return model


async def update_external_status(
    session: AsyncSession, user: User, update_data: ExternalStatusUpdate
) -> User:
    user.is_external_user = update_data.is_external
    await session.commit()
    await session.refresh(user)
    return user


async def _update_password(session: AsyncSession, user: User, password: str) -> User:
    user.password_hash = get_password_hash(password)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(
    session: AsyncSession, user: User, update_data: PasswordUpdate
) -> User:
    return await _update_password(session, user=user, password=update_data.password)


async def reset_user_password(session: AsyncSession, user: User) -> User:
    password = random_password()
    return await _update_password(session, user=user, password=password)


async def _get_permission(
    session: AsyncSession, *, client_application: ClientApplication, role: RoleType
) -> Permission | None:
    result = await session.execute(
        select(Permission).filter(
            and_(
                Permission.client_application_id == client_application.id,
                Permission.role == role,
            )
        )
    )
    return result.scalar_one_or_none()


async def _create_permission(
    session: AsyncSession, client_application: ClientApplication, role: RoleType
) -> Permission:
    db_obj = Permission(
        client_application_id=client_application.id,
        role=role,
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def list_permissions(
    session: AsyncSession, model: User | ClientApplication
) -> Sequence[Permission]:
    if isinstance(model, User):
        result = await session.execute(
            select(UserPermission).filter(UserPermission.user_id == model.id)
        )
    else:
        result = await session.execute(
            select(ClientApplicationPermission).filter(
                ClientApplicationPermission.client_application_id == model.id
            )
        )
    return [el.permission for el in result.scalars()]


async def add_permission(
    session: AsyncSession,
    model: User | ClientApplication,
    permission_data: PermissionUpdate,
) -> Permission:
    client_application = await get_client_application_by_name(
        session, name=permission_data.client_application
    )
    if not client_application:
        raise ClientApplicationNotFound(
            f"Client application {permission_data.client_application} not found"
        )

    permission = await _get_permission(
        session, client_application=client_application, role=permission_data.role
    )
    if not permission:
        permission = await _create_permission(
            session, client_application=client_application, role=permission_data.role
        )

    if isinstance(model, User):
        result = await session.execute(
            select(UserPermission).filter(
                and_(
                    UserPermission.user_id == model.id,
                    UserPermission.permission_id == permission.id,
                )
            )
        )

        client_application_permission = result.scalar_one_or_none()
        if client_application_permission:
            raise AlreadyAttachedPermission(
                f"Permission {permission} already attached to user {model.id}"
            )
        db_obj = UserPermission(user_id=model.id, permission_id=permission.id)
    else:
        result = await session.execute(
            select(ClientApplicationPermission).filter(
                and_(
                    ClientApplicationPermission.client_application_id == model.id,
                    ClientApplicationPermission.permission_id == permission.id,
                )
            )
        )

        client_application_permission = result.scalar_one_or_none()
        if client_application_permission:
            raise AlreadyAttachedPermission(
                f"Permission {permission} already attached to client application {model.id}"
            )
        db_obj = ClientApplicationPermission(
            client_application_id=model.id, permission_id=permission.id
        )
    session.add(db_obj)
    await session.commit()

    return permission


async def remove_permission(
    session: AsyncSession, model: User | ClientApplication, permission_id: int
) -> None:
    if isinstance(model, User):
        await session.execute(
            delete(UserPermission).where(
                UserPermission.user_id == model.id,
                UserPermission.permission_id == permission_id,
            )
        )
    else:
        await session.execute(
            delete(ClientApplicationPermission).where(
                ClientApplicationPermission.client_application_id == model.id,
                ClientApplicationPermission.permission_id == permission_id,
            )
        )
    await session.commit()
