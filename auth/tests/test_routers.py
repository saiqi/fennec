from typing import AsyncGenerator, Callable, Any
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


@pytest.fixture
def permission_factory(
    self_read_permission: Permission,
    self_write_permission: Permission,
    self_admin_permission: Permission,
) -> Callable[[str], Permission]:
    def _inner(p: str) -> Permission:
        if p not in {"read", "write", "admin"}:
            raise ValueError(f"Unkown permission {p}")

        if p == "read":
            return self_read_permission
        elif p == "write":
            return self_write_permission
        else:
            return self_admin_permission

    return _inner


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


test_cases = [
    # --- Groups endpoints ---
    # Internal user with read should succeed in GET groups
    ("/api/v1/groups", "GET", "read", False, None, 200),
    # External user with read should be forbidden in GET groups
    ("/api/v1/groups", "GET", "read", True, None, 403),
    # Internal user with admin can create a group
    ("/api/v1/groups", "POST", "admin", False, {"name": "besiktas"}, 201),
    # Internal user with read cannot create a group
    ("/api/v1/groups", "POST", "read", False, {"name": "besiktas"}, 403),
    # External user with admin cannot create a group
    ("/api/v1/groups", "POST", "admin", True, {"name": "besiktas"}, 403),
    # Internal user with admin cannot create an existing group
    ("/api/v1/groups", "POST", "admin", False, {"name": "red-star"}, 400),
    # --- Users endpoints ---
    # Internal user with read should succeed in GET users
    ("/api/v1/users", "GET", "read", False, None, 200),
    # External user with read should be forbidden in GET users
    ("/api/v1/users", "GET", "read", True, None, 403),
    # Any user should succeed in GET me
    ("/api/v1/users/me", "GET", "read", True, None, 200),
    # Internal user with read should succeed in GET users by name
    ("/api/v1/users/fleury", "GET", "read", False, None, 200),
    # External user with read should be forbidden in GET users by name
    ("/api/v1/users/fleury", "GET", "read", True, None, 403),
    # Internal user with read should fail in GET users by name when user is not known
    ("/api/v1/users/unknown", "GET", "read", False, None, 404),
    # Internal user with admin can update a user's group
    ("/api/v1/users/fleury/groups", "PUT", "admin", False, {"name": "red-star"}, 200),
    # Internal user with admin cannot update a user's group to an unkwnown group
    ("/api/v1/users/fleury/groups", "PUT", "admin", False, {"name": "unknown"}, 404),
    # Internal user with read cannot update a user's group
    ("/api/v1/users/fleury/groups", "PUT", "read", False, {"name": "red-star"}, 403),
    # External user with admin can update a user's group
    ("/api/v1/users/fleury/groups", "PUT", "admin", True, {"name": "red-star"}, 403),
    # Internal user with admin can update a user's activity status
    (
        "/api/v1/users/fleury/activity-status",
        "PUT",
        "admin",
        False,
        {"is_active": False},
        200,
    ),
    # Internal user with read cannot update a user's activity status
    (
        "/api/v1/users/fleury/activity-status",
        "PUT",
        "read",
        False,
        {"is_active": False},
        403,
    ),
    # External user with admin cannot update a user's activity status
    (
        "/api/v1/users/fleury/activity-status",
        "PUT",
        "admin",
        True,
        {"is_active": False},
        403,
    ),
    # Internal user with admin can update a user's external status
    (
        "/api/v1/users/fleury/external-status",
        "PUT",
        "admin",
        False,
        {"is_external": False},
        200,
    ),
    # Internal user with read cannot update a user's external status
    (
        "/api/v1/users/fleury/external-status",
        "PUT",
        "read",
        False,
        {"is_external": False},
        403,
    ),
    # External user with admin cannot update a user's external status
    (
        "/api/v1/users/fleury/external-status",
        "PUT",
        "admin",
        True,
        {"is_external": False},
        403,
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint, method, permission_required, is_external, req_body, expected_status",
    test_cases,
)
async def test_endpoint_permissions(
    session: AsyncSession,
    test_client: AsyncClient,
    existing_user: User,
    permission_factory: Callable[[str], Permission],
    endpoint: str,
    method: str,
    permission_required: str,
    is_external: bool,
    req_body: dict[str, Any],
    expected_status: int,
) -> None:
    permission = permission_factory(permission_required)
    existing_user.permissions.append(permission)
    existing_user.is_external = is_external
    await session.commit()

    headers = create_self_headers(existing_user, permission_required)

    if method.upper() == "GET":
        resp = await test_client.get(endpoint, headers=headers)
    elif method.upper() == "POST":
        resp = await test_client.post(endpoint, headers=headers, json=req_body)
    elif method.upper() == "PUT":
        resp = await test_client.put(endpoint, headers=headers, json=req_body)
    elif method.upper() == "DELETE":
        resp = await test_client.delete(endpoint, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    assert resp.status_code == expected_status
