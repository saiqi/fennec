import pytest
from httpx import AsyncClient
from fennec_api.users.models import User


@pytest.mark.asyncio
async def test_register_user(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/v1/users",
        json={"email": "rino.dellanegra@redstarfc.fr", "password": "password"},
    )
    assert resp.status_code == 201
    assert resp.json() == {
        "id": 1,
        "email": "rino.dellanegra@redstarfc.fr",
        "role": "read",
        "disabled": False,
    }


@pytest.mark.asyncio
async def test_register_existing_user(
    test_client: AsyncClient, existing_user: User
) -> None:
    resp = await test_client.post(
        "/api/v1/users",
        json={"email": existing_user.email, "password": "password"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_read_me(test_client: AsyncClient, existing_user_token: str) -> None:
    resp = await test_client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {existing_user_token}"}
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_list_users(
    test_client: AsyncClient, existing_admin_token: str
) -> None:
    resp = await test_client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {existing_admin_token}"}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_list_users_is_forbidden(
    test_client: AsyncClient, existing_user_token: str
) -> None:
    resp = await test_client.get(
        "/api/v1/users", headers={"Authorization": f"Bearer {existing_user_token}"}
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_password(
    test_client: AsyncClient, existing_user_token: str
) -> None:
    resp = await test_client.post(
        "/api/v1/users/1/update-password",
        json={"password": "new-password"},
        headers={"Authorization": f"Bearer {existing_user_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_can_update_user_status(
    test_client: AsyncClient, existing_admin_token: str, existing_user: User
) -> None:
    resp = await test_client.post(
        f"/api/v1/users/{existing_user.id}/update-status",
        json={"disabled": True},
        headers={"Authorization": f"Bearer {existing_admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_update_user_status_is_forbidden(
    test_client: AsyncClient, existing_user_token: str, existing_user: User
) -> None:
    resp = await test_client.post(
        f"/api/v1/users/{existing_user.id}/update-status",
        json={"disabled": True},
        headers={"Authorization": f"Bearer {existing_user_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_update_user_role(
    test_client: AsyncClient, existing_admin_token: str, existing_user: User
) -> None:
    resp = await test_client.post(
        f"/api/v1/users/{existing_user.id}/update-role",
        json={"role": "write"},
        headers={"Authorization": f"Bearer {existing_admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_update_user_role_is_forbidden(
    test_client: AsyncClient, existing_user_token: str, existing_user: User
) -> None:
    resp = await test_client.post(
        f"/api/v1/users/{existing_user.id}/update-status",
        json={"role": "write"},
        headers={"Authorization": f"Bearer {existing_user_token}"},
    )
    assert resp.status_code == 403
