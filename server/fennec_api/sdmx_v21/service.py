from typing import Callable
from itertools import groupby
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
    CodedStatusMessageType,
    DataflowType,
    DataStructureType2,
    CategorySchemeType,
    CategorisationType,
    Attribute2,
    Dimension2,
    TimeDimension2,
    PrimaryMeasure2,
    RefBaseType,
    PackageTypeCodelistType,
    ObjectTypeCodelistType,
    CodelistType,
    ConceptSchemeType,
)
from fennec_api.sdmx_v21.exceptions import SDMXRestProviderError


def _to_error_message(error: Error) -> str:
    def handle_message(m: CodedStatusMessageType) -> str:
        return f"{m.code}: {','.join(el.value for el in m.text)}"

    return "\n".join(map(handle_message, error.error_message))


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
    try:
        msg = await client.get_structure(req=req)
    except Exception as e:
        raise SDMXRestProviderError(e)

    try:
        structure = parse_structure(msg)
    except Exception as e:
        raise SDMXRestProviderError(e)

    if isinstance(structure, Error):
        raise SDMXRestProviderError(_to_error_message(structure))

    return structure


async def fetch_all_dataflows(
    client: SDMX21RestClient, agency_id: str | None = None
) -> list[DataflowType]:
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
) -> list[CategorySchemeType]:
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
) -> list[CategorisationType]:
    msg = await fetch_structure(
        client=client,
        req=SDMX21StructureRequest(
            resource=StructureType.CATEGORISATION, agency_id=agency_id
        ),
    )
    if not msg.structures or not msg.structures.categorisations:
        raise SDMXRestProviderError("No categorisation found")
    return msg.structures.categorisations.categorisation


async def fetch_data_structure(
    client: SDMX21RestClient, dataflow: DataflowType
) -> DataStructureType2:
    if not dataflow.structure or not dataflow.structure.ref:
        raise SDMXRestProviderError("No data structure reference found")
    req = _to_structure_req(dataflow.structure.ref)
    msg = await fetch_structure(client=client, req=req)
    if (
        not msg.structures
        or not msg.structures.data_structures
        or not msg.structures.data_structures.data_structure
    ):
        raise SDMXRestProviderError("No data structure found")
    return msg.structures.data_structures.data_structure[0]


def _extract_refs(
    data_structure: DataStructureType2,
    extractor: Callable[
        [Attribute2 | Dimension2 | TimeDimension2 | PrimaryMeasure2], RefBaseType | None
    ],
) -> list[RefBaseType]:
    def extract_refs(
        list_: list[Attribute2]
        | list[Dimension2]
        | list[TimeDimension2]
        | list[PrimaryMeasure2],
    ) -> list[RefBaseType]:
        return [ref for el in list_ if (ref := extractor(el)) is not None]

    if not data_structure.data_structure_components:
        raise SDMXRestProviderError("No data structure components found")

    refs: list[RefBaseType] = []
    if data_structure.data_structure_components.dimension_list:
        refs.extend(
            extract_refs(
                data_structure.data_structure_components.dimension_list.dimension
            )
        )
        refs.extend(
            extract_refs(
                data_structure.data_structure_components.dimension_list.time_dimension
            )
        )
    if data_structure.data_structure_components.attribute_list:
        refs.extend(
            extract_refs(
                data_structure.data_structure_components.attribute_list.attribute
            )
        )
    if (
        data_structure.data_structure_components.measure_list
        and data_structure.data_structure_components.measure_list.primary_measure
    ):
        measure_ref = extractor(
            data_structure.data_structure_components.measure_list.primary_measure
        )
        if measure_ref:
            refs.append(measure_ref)

    def keyfunc(ref: RefBaseType) -> tuple[str | None, str | None, str | None]:
        return (ref.id, ref.agency_id, ref.version)

    return [k for k, _ in groupby(sorted(refs, key=keyfunc))]


async def _fetch_from_refs(
    client: SDMX21RestClient, refs: list[RefBaseType]
) -> list[Structure]:
    reqs = [_to_structure_req(ref) for ref in refs]
    return await asyncio.gather(
        *(fetch_structure(client=client, req=req) for req in reqs)
    )


async def fetch_codelists(
    client: SDMX21RestClient, data_structure: DataStructureType2
) -> list[CodelistType]:
    def extract_codelist(
        component: Attribute2 | Dimension2 | TimeDimension2 | PrimaryMeasure2,
    ) -> RefBaseType | None:
        if (
            not component.local_representation
            or not component.local_representation.enumeration
        ):
            return None
        return component.local_representation.enumeration.ref

    refs = _extract_refs(data_structure, extract_codelist)
    results = await _fetch_from_refs(client, refs)
    return [
        cl
        for r in results
        if r.structures and r.structures.codelists
        for cl in r.structures.codelists.codelist
    ]


async def fetch_concept_schemes(
    client: SDMX21RestClient, data_structure: DataStructureType2
) -> list[ConceptSchemeType]:
    def extract_concept(
        component: Attribute2 | Dimension2 | TimeDimension2 | PrimaryMeasure2,
    ) -> RefBaseType | None:
        if not component.concept_identity:
            return None
        return component.concept_identity.ref

    refs = _extract_refs(data_structure, extract_concept)
    results = await _fetch_from_refs(client, refs)
    return [
        c
        for r in results
        if r.structures and r.structures.concepts
        for c in r.structures.concepts.concept_scheme
    ]
