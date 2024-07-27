from typing import AsyncGenerator
import pytest
import pytest_asyncio
import aiofiles
import httpx
from fennec_api.sdmx_v21.client import (
    SDMX21RestClient,
)
import fennec_api.sdmx_v21.service as service


@pytest_asyncio.fixture()
async def mock_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async def open_fixture(req: httpx.Request) -> httpx.Response:
        if "categorisation" in req.url.path:
            path = "data/sdmxml21/categorisation.xml"
        elif "categoryscheme" in req.url.path:
            path = "data/sdmxml21/categoryscheme.xml"
        elif "codelist" in req.url.path:
            path = "data/sdmxml21/codelist.xml"
        elif "conceptscheme" in req.url.path:
            path = "data/sdmxml21/conceptscheme.xml"
        elif "contentconstraint" in req.url.path:
            path = "data/sdmxml21/contentconstraint.xml"
        elif "dataflow" in req.url.path:
            path = "data/sdmxml21/dataflow.xml"
        elif "datastructure" in req.url.path:
            path = "data/sdmxml21/datastructure.xml"
        else:
            raise NotImplementedError

        async with aiofiles.open(path, "rb") as f:
            content: bytes = await f.read()
            return httpx.Response(200, content=content)

    async with httpx.AsyncClient(transport=httpx.MockTransport(open_fixture)) as client:
        yield client


@pytest_asyncio.fixture()
async def mock_sdmx_client(
    mock_http_client: httpx.AsyncClient,
) -> AsyncGenerator[SDMX21RestClient, None]:
    yield SDMX21RestClient(http_client=mock_http_client, root_url="http://test")


@pytest.mark.asyncio
async def test_crawl_structures(mock_sdmx_client: SDMX21RestClient) -> None:
    dataflows = await service.fetch_all_dataflows(client=mock_sdmx_client)
    await service.fetch_all_categorisations(client=mock_sdmx_client)
    await service.fetch_all_category_schemes(client=mock_sdmx_client)

    dataflow = dataflows[0]
    data_structure = await service.fetch_data_structure(
        client=mock_sdmx_client, dataflow=dataflow
    )

    await service.fetch_codelists(
        client=mock_sdmx_client, data_structure=data_structure
    )
    await service.fetch_concept_schemes(
        client=mock_sdmx_client, data_structure=data_structure
    )
