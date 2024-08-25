from typing import Iterable, Sequence
import asyncio
from fennec_api.sdmx_v21.client import (
    SDMX21RestClient,
    SDMX21StructureRequest,
    StructureType,
)
from fennec_api.sdmx_v21.parser import (
    parse_structure,
    Structure,
    Error,
    DataflowType,
    DataStructureType2,
    CategorySchemeType,
    CategorisationType,
    RefBaseType,
    PackageTypeCodelistType,
    ObjectTypeCodelistType,
    CodelistType,
    ConceptSchemeType,
)
from fennec_api.sdmx_v21.exceptions import SDMXRestProviderError


def _to_structure_req(ref: RefBaseType) -> SDMX21StructureRequest:
    if (
        ref.package == PackageTypeCodelistType.DATASTRUCTURE
        and ref.class_value == ObjectTypeCodelistType.DATA_STRUCTURE
    ):
        return SDMX21StructureRequest(
            resource=StructureType.DATASTRUCTURE,
            agency_id=ref.agency_id,
            resource_id=ref.id,
            version=ref.version,
        )

    if (
        ref.package == PackageTypeCodelistType.DATASTRUCTURE
        and ref.class_value == ObjectTypeCodelistType.DATAFLOW
    ):
        return SDMX21StructureRequest(
            resource=StructureType.DATAFLOW,
            agency_id=ref.agency_id,
            resource_id=ref.id,
            version=ref.version,
        )

    if (
        ref.package == PackageTypeCodelistType.CODELIST
        and ref.class_value == ObjectTypeCodelistType.CODELIST
    ):
        return SDMX21StructureRequest(
            resource=StructureType.CODELIST,
            agency_id=ref.agency_id,
            resource_id=ref.id,
            version=ref.version,
        )

    if (
        ref.package == PackageTypeCodelistType.CONCEPTSCHEME
        and ref.class_value == ObjectTypeCodelistType.CONCEPT
    ):
        return SDMX21StructureRequest(
            resource=StructureType.CONCEPTSCHEME,
            agency_id=ref.agency_id,
            resource_id=ref.maintainable_parent_id,
            version=ref.maintainable_parent_version,
        )

    if (
        ref.package == PackageTypeCodelistType.CATEGORYSCHEME
        and ref.class_value == ObjectTypeCodelistType.CATEGORY_SCHEME
    ):
        return SDMX21StructureRequest(
            resource=StructureType.CATEGORYSCHEME,
            agency_id=ref.agency_id,
            resource_id=ref.maintainable_parent_id,
            version=ref.maintainable_parent_version,
        )
    raise SDMXRestProviderError(f"Cannot find corresponding REST endpoint of {ref}")


async def fetch_structure(
    client: SDMX21RestClient, req: SDMX21StructureRequest
) -> Structure:
    msg = await client.get_structure(req=req)
    structure = parse_structure(msg)

    if isinstance(structure, Error):
        raise SDMXRestProviderError(msg.decode())

    return structure


async def fetch_all_dataflows(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[DataflowType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.DATAFLOW, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.dataflows:
        raise SDMXRestProviderError("No dataflow found")
    return msg.structures.dataflows.dataflow


async def fetch_all_category_schemes(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[CategorySchemeType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.CATEGORYSCHEME, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.category_schemes:
        raise SDMXRestProviderError("No category scheme found")
    return msg.structures.category_schemes.category_scheme


async def fetch_all_categorisations(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[CategorisationType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.CATEGORISATION, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.categorisations:
        raise SDMXRestProviderError("No categorisation found")
    return msg.structures.categorisations.categorisation


async def fetch_all_codelists(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[CodelistType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.CODELIST, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.codelists:
        raise SDMXRestProviderError("No codelist found")
    return msg.structures.codelists.codelist


async def fetch_all_concept_schemes(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[ConceptSchemeType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.CONCEPTSCHEME, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.concepts:
        raise SDMXRestProviderError("No concept scheme found")
    return msg.structures.concepts.concept_scheme


async def fetch_all_data_structures(
    client: SDMX21RestClient, agency_id: str | None = None
) -> Sequence[DataStructureType2]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.DATASTRUCTURE, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.data_structures:
        raise SDMXRestProviderError("No data structure found")
    return msg.structures.data_structures.data_structure


async def fetch_data_structure(
    client: SDMX21RestClient, ref: RefBaseType
) -> DataStructureType2:
    req = _to_structure_req(ref)
    msg = await fetch_structure(client=client, req=req)
    if (
        not msg.structures
        or not msg.structures.data_structures
        or not msg.structures.data_structures.data_structure
    ):
        raise SDMXRestProviderError("No data structure found")
    return msg.structures.data_structures.data_structure[0]


async def _fetch_from_refs(
    client: SDMX21RestClient, refs: Iterable[RefBaseType]
) -> Sequence[Structure]:
    reqs = [_to_structure_req(ref) for ref in refs]
    return await asyncio.gather(
        *(fetch_structure(client=client, req=req) for req in reqs)
    )


async def fetch_codelists(
    client: SDMX21RestClient, refs: Iterable[RefBaseType]
) -> Sequence[CodelistType]:
    results = await _fetch_from_refs(client, refs)
    return [
        cl
        for r in results
        if r.structures and r.structures.codelists
        for cl in r.structures.codelists.codelist
    ]


async def fetch_concept_schemes(
    client: SDMX21RestClient, refs: Iterable[RefBaseType]
) -> Sequence[ConceptSchemeType]:
    results = await _fetch_from_refs(client, refs)
    return [
        c
        for r in results
        if r.structures and r.structures.concepts
        for c in r.structures.concepts.concept_scheme
    ]
