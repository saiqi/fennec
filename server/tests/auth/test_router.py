import pytest
from httpx import AsyncClient
from fennec_api.users.models import User


@pytest.mark.asyncio
async def test_existing_user_can_login_for_token(
    test_client: AsyncClient, existing_user: User
) -> None:
    r = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "",
            "username": existing_user.email,
            "password": "password",
            "scope": "",
            "client_id": "",
            "client_secret": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_unknown_user_can_login_for_token(test_client: AsyncClient) -> None:
    r = await test_client.post(
        "/api/v1/auth/token",
        data={
            "grant_type": "",
            "username": "unknown@example.org",
            "password": "password",
            "scope": "",
            "client_id": "",
            "client_secret": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401
