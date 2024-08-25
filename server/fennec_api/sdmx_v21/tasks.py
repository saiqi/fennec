from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from arq.connections import ArqRedis
from fennec_api.sdmx_v21.client import SDMX21RestClient
import fennec_api.sdmx_v21.etl as etl
import fennec_api.sdmx_v21.service as service


async def collect_provider(ctx: dict[str, Any], provider_id: int) -> None:
    session: AsyncSession = ctx["session"]

    provider = await service.get_provider(session, id=provider_id)

    if not provider:
        return

    agency_id = provider.agency_id if not provider.process_all_agencies else None

    async with AsyncClient() as http_client:
        sdmx_client = SDMX21RestClient(
            http_client=http_client, root_url=provider.root_url
        )
        dataflows = await etl.fetch_all_dataflows(sdmx_client, agency_id)
        await etl.load_dataflows(session, dataflows)

        if provider.bulk_download:
            dsds = await etl.fetch_all_data_structures(sdmx_client, agency_id)
            await etl.load_data_structures(session, dsds)

            codelists = await etl.fetch_all_codelists(sdmx_client, agency_id)
            await etl.load_codelists(session, codelists)

            concept_schemes = await etl.fetch_all_concept_schemes(
                sdmx_client, agency_id
            )
            await etl.load_concept_schemes(session, concept_schemes)
        else:
            dsds = [
                await etl.fetch_data_structure(sdmx_client, ref)
                for ref in etl.extract_data_structure_refs(dataflows)
            ]
            await etl.load_data_structures(session, dsds)

            codelists = await etl.fetch_codelists(
                sdmx_client, etl.extract_codelist_refs(dsds)
            )
            await etl.load_codelists(session, codelists)

            concept_schemes = await etl.fetch_concept_schemes(
                sdmx_client, etl.extract_concept_refs(dsds)
            )
            await etl.load_concept_schemes(session, concept_schemes)

        if not provider.skip_categories:
            categorisations = await etl.fetch_all_categorisations(
                sdmx_client, agency_id
            )
            await etl.load_categorisations(session, categorisations)
            category_schemes = await etl.fetch_all_category_schemes(
                sdmx_client, agency_id
            )
            await etl.load_category_schemes(session, category_schemes)


async def collect_metadata(ctx: dict[str, Any]) -> None:
    session: AsyncSession = ctx["session"]
    redis: ArqRedis = ctx["redis"]

    providers = await service.list_providers(session, offset=0, limit=-1)

    for provider in providers:
        await redis.enqueue_job("collect_provider", provider.id)
