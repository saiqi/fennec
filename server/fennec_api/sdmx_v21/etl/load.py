from typing import Any, Sequence
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_api.etl.postgres import upsert
from fennec_api.sdmx_v21.parser import (
    DataflowType,
    DataStructureType2,
    Attribute2,
    Dimension2,
    TimeDimension2,
    PrimaryMeasure2,
    CategorySchemeType,
    CodelistType,
    ConceptSchemeType,
    CategorisationType,
    ComponentType,
)
from fennec_api.sdmx_v21.models import (
    Dataflow,
    DataStructure,
    TimeDimension,
    Dimension,
    Attribute,
    PrimaryMeasure,
    CategoryScheme,
    Category,
    Codelist,
    Code,
    ConceptScheme,
    Concept,
    Categorisation,
)
from fennec_api.sdmx_v21.etl.transform import flatten_categories, extract_labels


async def load_dataflows(
    session: AsyncSession, dataflows: Sequence[DataflowType]
) -> None:
    records = (
        {
            "id": df.id,
            "agency_id": df.agency_id,
            "version": df.version,
            "urn": df.urn,
            **extract_labels(df),
            "structure_id": df.structure.ref.id,
            "structure_agency_id": df.structure.ref.agency_id,
            "structure_version": df.structure.ref.version,
            "structure_package": df.structure.ref.package.value
            if df.structure.ref.package
            else None,
            "structure_class": df.structure.ref.class_value.value
            if df.structure.ref.class_value
            else None,
        }
        for df in dataflows
        if df.structure and df.structure.ref
    )

    await upsert(session, model=Dataflow, records=records)


async def load_data_structures(
    session: AsyncSession, data_structures: Sequence[DataStructureType2]
) -> None:
    def extract_concept(
        r: ComponentType,
    ) -> dict[str, Any]:
        if not r.concept_identity or not r.concept_identity.ref:
            return defaultdict(lambda: None)
        ref = r.concept_identity.ref
        return dict(
            concept_id=ref.id,
            concept_maintainable_parent_id=ref.maintainable_parent_id,
            concept_maintainable_parent_version=ref.maintainable_parent_version,
            concept_agency_id=ref.agency_id,
            concept_package=ref.package.value if ref.package else None,
            concept_class=ref.class_value.value if ref.class_value else None,
        )

    def extract_repr(
        r: ComponentType,
    ) -> dict[str, Any]:
        if not r.local_representation:
            return defaultdict(lambda: None)

        repr = r.local_representation

        if repr.text_format:
            return dict(
                format_type=repr.text_format.text_type.value,
                codelist_id=None,
                codelist_agency_id=None,
                codelist_version=None,
                codelist_package=None,
                codelist_class=None,
            )
        if not repr.enumeration or not repr.enumeration.ref:
            return defaultdict(lambda: None)
        return dict(
            format_type=None,
            codelist_id=repr.enumeration.ref.id,
            codelist_agency_id=repr.enumeration.ref.agency_id,
            codelist_version=repr.enumeration.ref.version,
            codelist_package=repr.enumeration.ref.package.value
            if repr.enumeration.ref.package
            else None,
            codelist_class=repr.enumeration.ref.class_value.value
            if repr.enumeration.ref.class_value
            else None,
        )

    def to_component_record(
        data_structure: DataStructureType2,
        r: ComponentType,
    ) -> dict[str, Any]:
        obj: dict[str, Any] = dict(
            id=r.id,
            urn=r.urn,
            data_structure_id=data_structure.id,
            data_structure_agency_id=data_structure.agency_id,
            data_structure_version=data_structure.version,
        )
        obj.update(extract_concept(r))

        if not isinstance(r, PrimaryMeasure2):
            obj.update(extract_repr(r))

        if isinstance(r, Dimension2) or isinstance(r, TimeDimension2):
            obj["position"] = r.position

        if isinstance(r, Attribute2):
            obj["assignment_status"] = (
                r.assignment_status.value if r.assignment_status else None
            )

        return obj

    data_structure_records = (
        dict(
            id=data_structure.id,
            agency_id=data_structure.agency_id,
            version=data_structure.version,
            urn=data_structure.urn,
            **extract_labels(data_structure),
        )
        for data_structure in data_structures
    )
    await upsert(session, model=DataStructure, records=data_structure_records)

    time_dimension_records = (
        to_component_record(data_structure, td)
        for data_structure in data_structures
        if data_structure.data_structure_components
        and data_structure.data_structure_components.dimension_list
        for td in data_structure.data_structure_components.dimension_list.time_dimension
    )
    await upsert(session, model=TimeDimension, records=time_dimension_records)

    dimension_records = (
        to_component_record(data_structure, d)
        for data_structure in data_structures
        if data_structure.data_structure_components
        and data_structure.data_structure_components.dimension_list
        for d in data_structure.data_structure_components.dimension_list.dimension
    )
    await upsert(session, model=Dimension, records=dimension_records)

    attribute_records = (
        to_component_record(data_structure, a)
        for data_structure in data_structures
        if data_structure.data_structure_components
        and data_structure.data_structure_components.attribute_list
        for a in data_structure.data_structure_components.attribute_list.attribute
    )
    await upsert(session, model=Attribute, records=attribute_records)

    measure_records = (
        to_component_record(
            data_structure,
            data_structure.data_structure_components.measure_list.primary_measure,
        )
        for data_structure in data_structures
        if data_structure.data_structure_components
        and data_structure.data_structure_components.measure_list
        and data_structure.data_structure_components.measure_list.primary_measure
    )
    await upsert(session, model=PrimaryMeasure, records=measure_records)


async def load_category_schemes(
    session: AsyncSession, category_schemes: Sequence[CategorySchemeType]
) -> None:
    scheme_records = (
        {
            "id": cs.id,
            "agency_id": cs.agency_id,
            "version": cs.version,
            "urn": cs.urn,
            **extract_labels(cs),
        }
        for cs in category_schemes
    )
    await upsert(session, model=CategoryScheme, records=scheme_records)

    category_records = (
        {
            "id": c.id,
            "urn": c.urn,
            **extract_labels(c),
            "category_scheme_id": cs.id,
            "category_scheme_agency_id": cs.agency_id,
            "category_scheme_version": cs.version,
            "parent_id": parent_id,
            "parent_scheme_id": cs.id if parent_id else None,
            "parent_scheme_agency_id": cs.agency_id if parent_id else None,
            "parent_scheme_version": cs.version if parent_id else None,
        }
        for cs in category_schemes
        if cs.id and cs.agency_id and cs.version
        for _, _, _, parent_id, c in flatten_categories(
            cs.category,
            scheme_id=cs.id,
            scheme_agency_id=cs.agency_id,
            scheme_version=cs.version,
        )
    )
    await upsert(session, model=Category, records=category_records)


async def load_codelists(
    session: AsyncSession, codelists: Sequence[CodelistType]
) -> None:
    codelist_records = (
        {
            "id": cl.id,
            "agency_id": cl.agency_id,
            "version": cl.version,
            "urn": cl.urn,
            **extract_labels(cl),
        }
        for cl in codelists
    )
    await upsert(session, model=Codelist, records=codelist_records)

    code_records = (
        {
            "id": c.id,
            "urn": c.urn,
            **extract_labels(c),
            "codelist_id": cl.id,
            "codelist_agency_id": cl.agency_id,
            "codelist_version": cl.version,
        }
        for cl in codelists
        for c in cl.code
    )
    await upsert(session, model=Code, records=code_records)


async def load_concept_schemes(
    session: AsyncSession, concept_schemes: Sequence[ConceptSchemeType]
) -> None:
    concept_scheme_records = (
        {
            "id": cs.id,
            "agency_id": cs.agency_id,
            "version": cs.version,
            "urn": cs.urn,
            **extract_labels(cs),
        }
        for cs in concept_schemes
    )
    await upsert(session, model=ConceptScheme, records=concept_scheme_records)

    concept_records = (
        {
            "id": c.id,
            "urn": c.urn,
            **extract_labels(c),
            "concept_scheme_id": cs.id,
            "concept_scheme_agency_id": cs.agency_id,
            "concept_scheme_version": cs.version,
        }
        for cs in concept_schemes
        for c in cs.concept
    )
    await upsert(session, model=Concept, records=concept_records)


async def load_categorisations(
    session: AsyncSession, categorisations: Sequence[CategorisationType]
) -> None:
    categorisation_records = (
        {
            "id": c.id,
            "agency_id": c.agency_id,
            "version": c.version,
            "urn": c.urn,
            **extract_labels(c),
            "source_id": c.source.ref.id,
            "source_agency_id": c.source.ref.agency_id,
            "source_version": c.source.ref.version,
            "source_package": c.source.ref.package.value
            if c.source.ref.package
            else None,
            "source_class": c.source.ref.class_value.value
            if c.source.ref.class_value
            else None,
            "target_id": c.target.ref.id,
            "maintainable_parent_id": c.target.ref.maintainable_parent_id,
            "maintainable_parent_version": c.target.ref.maintainable_parent_version,
            "target_agency_id": c.target.ref.agency_id,
            "target_package": c.target.ref.package.value
            if c.target.ref.package
            else None,
            "target_class": c.target.ref.class_value.value
            if c.target.ref.class_value
            else None,
        }
        for c in categorisations
        if c.source and c.source.ref and c.target and c.target.ref
    )
    await upsert(session, model=Categorisation, records=categorisation_records)
