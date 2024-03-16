from typing import AsyncGenerator
import pytest
import pytest_asyncio
import aiofiles
import httpx
from fennec_api.sdmx_v21.client import (
    SDMX21RestClient,
    SDMX21StructureRequest,
    StructureType,
    build_default_structure_path,
    build_default_structure_params,
    build_default_structure_headers,
    ReferencesType,
    DetailType,
)


@pytest_asyncio.fixture()
async def mock_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with aiofiles.open("data/sdmxml21/dataflow.xml", "rb") as f:
        content = await f.read()
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda req: httpx.Response(200, content=content)
            )
        ) as client:
            yield client


def test_default_structure_path_builder() -> None:
    req_by_resource_id = SDMX21StructureRequest(
        resource=StructureType.DATAFLOW,
        agency_id="FR1",
        resource_id="BALANCE-PAIEMENTS",
    )
    assert (
        build_default_structure_path(req_by_resource_id)
        == "dataflow/FR1/BALANCE-PAIEMENTS"
    )

    req_all_resources = SDMX21StructureRequest(
        resource=StructureType.DATAFLOW,
        agency_id="FR1",
    )
    assert build_default_structure_path(req_all_resources) == "dataflow/FR1"

    req_by_item_id = SDMX21StructureRequest(
        resource=StructureType.CODELIST,
        agency_id="FR1",
        resource_id="CL_FREQ",
        version="latest",
        item_id="A",
    )
    assert (
        build_default_structure_path(req_by_item_id) == "codelist/FR1/CL_FREQ/latest/A"
    )


def test_default_structure_params_builder() -> None:
    assert build_default_structure_params(None, None) == {}
    assert build_default_structure_params(DetailType.ALLSTUBS, None) == {
        "detail": "allstubs"
    }
    assert build_default_structure_params(None, ReferencesType.NONE) == {
        "references": "none"
    }
    assert build_default_structure_params(DetailType.ALLSTUBS, ReferencesType.NONE) == {
        "detail": "allstubs",
        "references": "none",
    }


def test_default_structure_headers_builder() -> None:
    assert build_default_structure_headers() == {
        "Accept": "application/vnd.sdmx.structure+xml;version=2.1"
    }


@pytest.mark.asyncio
async def test_get_structure_by_resource_id(
    mock_http_client: httpx.AsyncClient,
) -> None:
    req = SDMX21StructureRequest(
        resource=StructureType.DATAFLOW,
        agency_id="FR1",
        resource_id="BALANCE-PAIEMENTS",
    )
    client = SDMX21RestClient(
        http_client=mock_http_client, root_url="https://sdmx-rest"
    )
    message = await client.get_structure(req=req)
    assert message
