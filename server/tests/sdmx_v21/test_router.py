from typing import Any
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fennec_api.sdmx_v21.models import Provider
from fennec_api.sdmx_v21.schemas import ProviderCreate
from fennec_api.sdmx_v21.service import create_provider


@pytest.fixture()
def provider_data() -> dict[str, Any]:
    return {
        "agency_id": "FR1",
        "root_url": "https://www.bdm.insee.fr/series/sdmx",
        "bulk_download": True,
        "skip_categories": False,
        "process_all_agencies": False,
    }


@pytest_asyncio.fixture()
async def provider(session: AsyncSession, provider_data: dict[str, Any]) -> Provider:
    return await create_provider(
        session, obj_in=ProviderCreate.model_validate(provider_data)
    )


@pytest.mark.asyncio
async def test_create_provider(
    test_client: AsyncClient,
    session: AsyncSession,
    provider_data: dict[str, Any],
    existing_admin_token: str,
) -> None:
    r = await test_client.post(
        "/api/v1/sdmx/providers",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
        json=provider_data,
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_list_providers(
    test_client: AsyncClient,
    session: AsyncSession,
    provider: Provider,
    existing_admin_token: str,
) -> None:
    r = await test_client.get(
        "/api/v1/sdmx/providers",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_get_provider(
    test_client: AsyncClient,
    session: AsyncSession,
    provider: Provider,
    existing_admin_token: str,
) -> None:
    r = await test_client.get(
        f"/api/v1/sdmx/providers/{provider.id}",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_not_existing_provider(
    test_client: AsyncClient,
    session: AsyncSession,
    existing_admin_token: str,
) -> None:
    r = await test_client.get(
        "/api/v1/sdmx/providers/0",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_provider(
    test_client: AsyncClient,
    session: AsyncSession,
    provider: Provider,
    provider_data: dict[str, Any],
    existing_admin_token: str,
) -> None:
    r = await test_client.put(
        f"/api/v1/sdmx/providers/{provider.id}",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
        json=provider_data,
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_update_not_existing_provider(
    test_client: AsyncClient,
    session: AsyncSession,
    provider_data: dict[str, Any],
    existing_admin_token: str,
) -> None:
    r = await test_client.put(
        "/api/v1/sdmx/providers/0",
        headers={"Authorization": f"Bearer {existing_admin_token}"},
        json=provider_data,
    )
    assert r.status_code == 404
