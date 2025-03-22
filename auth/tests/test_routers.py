from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_auth.models import (
    User,
    ClientApplication,
    Permission,
    Group,
)
from fennec_auth.services import create_access_token
from fennec_auth.config import settings
from fennec_auth.security import get_password_hash


def create_self_headers(client: User | ClientApplication, role: str) -> dict[str, str]:
    token = create_access_token(client, scopes=[f"{settings.CLIENT_NAME}:{role}"])
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture()
async def read_permission(
    session: AsyncSession, existing_client_application: ClientApplication
) -> AsyncGenerator[Permission, None]:
    permission = Permission(
        role="read", client_application_id=existing_client_application.id
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    yield permission


@pytest_asyncio.fixture()
async def self_client_application(
    session: AsyncSession, existing_group: Group
) -> AsyncGenerator[ClientApplication, None]:
    client_application = ClientApplication(
        name=settings.CLIENT_NAME,
        client_id="self",
        client_secret_hash=get_password_hash("secret"),
        is_active=True,
        group_id=existing_group.id,
    )
    session.add(client_application)
    await session.commit()
    await session.refresh(client_application)
    yield client_application


@pytest_asyncio.fixture()
async def self_admin_permission(
    session: AsyncSession, self_client_application: ClientApplication
) -> AsyncGenerator[Permission, None]:
    permission = Permission(
        role="admin", client_application_id=self_client_application.id
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    yield permission


@pytest_asyncio.fixture()
async def self_read_permission(
    session: AsyncSession, self_client_application: ClientApplication
) -> AsyncGenerator[Permission, None]:
    permission = Permission(
        role="read", client_application_id=self_client_application.id
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    yield permission


@pytest_asyncio.fixture()
async def self_write_permission(
    session: AsyncSession, self_client_application: ClientApplication
) -> AsyncGenerator[Permission, None]:
    permission = Permission(
        role="write", client_application_id=self_client_application.id
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    yield permission


@pytest.mark.asyncio
async def test_login_password_flow_happy_path(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_user.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": existing_user.user_name,
            "password": "password",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_login_password_flow_failed_when_not_enough_permission(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_user.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": existing_user.user_name,
            "password": "password",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:write",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_password_flow_failed_when_missing_permission(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_user.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": existing_user.user_name,
            "password": "password",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:read {existing_alt_client_application.name}:read",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_password_flow_failed_when_scope_is_unknown(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_user.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": existing_user.user_name,
            "password": "password",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": "unknown:read",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_password_flow_failed_when_wrong_password(
    test_client: AsyncClient,
    existing_user: User,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
) -> None:
    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": existing_user.user_name,
            "password": "wrong",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_password_flow_failed_when_user_is_unknown(
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
) -> None:
    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "password",
            "username": "unknown",
            "password": "password",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_client_credentials_flow_happy_path(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_alt_client_application.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_login_client_credentials_flow_when_not_enough_permission(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_alt_client_application.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "secret",
            "scopes": f"{existing_client_application.name}:write",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login_client_credentials_flow_failed_when_wrong_secret(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_alt_client_application.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": existing_alt_client_application.client_id,
            "client_secret": "wrong",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_client_credentials_flow_failed_when_client_is_unknown(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_alt_client_application.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "unknown",
            "client_secret": "wrong",
            "scopes": f"{existing_client_application.name}:read",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_failed_when_scopes_is_invalid(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_client_application: ClientApplication,
    existing_alt_client_application: ClientApplication,
    read_permission: Permission,
) -> None:
    existing_alt_client_application.permissions.append(read_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "unknown",
            "client_secret": "wrong",
            "scopes": f"{existing_client_application.name}",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_user_internal_can_list_groups(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    self_read_permission: Permission,
) -> None:
    existing_user.permissions.append(self_read_permission)
    existing_user.is_external = False
    await session.commit()

    resp = await test_client.get(
        "/api/v1/groups",
        headers=create_self_headers(existing_user, "read"),
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_user_external_cannot_list_groups(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    self_read_permission: Permission,
) -> None:
    existing_user.permissions.append(self_read_permission)
    await session.commit()

    resp = await test_client.get(
        "/api/v1/groups",
        headers=create_self_headers(existing_user, "read"),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_internal_admin_can_create_group(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    self_admin_permission: Permission,
) -> None:
    existing_user.permissions.append(self_admin_permission)
    existing_user.is_external = False
    await session.commit()

    resp = await test_client.post(
        "/api/v1/groups",
        headers=create_self_headers(existing_user, "admin"),
        json={"name": "besiktas"},
    )

    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_user_internal_read_cannot_create_group(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    self_read_permission: Permission,
) -> None:
    existing_user.permissions.append(self_read_permission)
    existing_user.is_external = False
    await session.commit()

    resp = await test_client.post(
        "/api/v1/groups",
        headers=create_self_headers(existing_user, "read"),
        json={"name": "besiktas"},
    )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_external_admin_can_create_group(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    self_admin_permission: Permission,
) -> None:
    existing_user.permissions.append(self_admin_permission)
    await session.commit()

    resp = await test_client.post(
        "/api/v1/groups",
        headers=create_self_headers(existing_user, "admin"),
        json={"name": "besiktas"},
    )

    assert resp.status_code == 403
