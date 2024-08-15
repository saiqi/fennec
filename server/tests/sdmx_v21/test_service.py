from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
import pytest
import fennec_api.sdmx_v21.service as service
from fennec_api.sdmx_v21.schemas import ProviderCreate, ProviderUpdate


@pytest.fixture()
def provider_data() -> dict[str, Any]:
    return {
        "agency_id": "FR1",
        "root_url": "https://www.bdm.insee.fr/series/sdmx",
        "bulk_download": True,
        "skip_categories": False,
        "process_all_agencies": False,
    }


@pytest.mark.asyncio
async def test_manage_provider(
    session: AsyncSession, provider_data: dict[str, Any]
) -> None:
    created_provider = await service.create_provider(
        session, obj_in=ProviderCreate.model_validate(provider_data)
    )
    assert created_provider

    providers = await service.list_providers(session, offset=0, limit=100)
    assert len(providers) == 1

    provider = await service.get_provider(session, id=created_provider.id)
    assert provider

    updated_data = provider_data.copy()
    updated_data["root_url"] = "https://www.bdm.insee.fr/series/sdmx2"

    updated_provider = await service.update_provider(
        session, db_obj=provider, obj_in=ProviderUpdate.model_validate(updated_data)
    )
    assert updated_provider
    assert updated_provider.root_url == "https://www.bdm.insee.fr/series/sdmx2"
