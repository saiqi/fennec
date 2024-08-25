from typing import Iterable, Callable, Sequence
from functools import partial
from fennec_api.sdmx_v21.parser import (
    DataflowType,
    DataStructureType2,
    Category2,
    NameableType,
    RefBaseType,
    ComponentType,
)


def extract_labels(
    entity: NameableType,
) -> dict[str, str | None]:
    return {
        "name": next((n.value for n in entity.name if n.lang == "en"), None),
        "description": next(
            (n.value for n in entity.description if n.lang == "en"), None
        ),
    }


def flatten_categories(
    categories: Sequence[Category2],
    *,
    scheme_id: str,
    scheme_agency_id: str,
    scheme_version: str,
    parent_id: str | None = None,
) -> Iterable[tuple[str, str, str, str | None, Category2]]:
    for c in categories:
        yield scheme_id, scheme_agency_id, scheme_version, parent_id, c
        yield from flatten_categories(
            c.category,
            scheme_id=scheme_id,
            scheme_agency_id=scheme_agency_id,
            scheme_version=scheme_version,
            parent_id=c.id,
        )


def unique_by_ref(
    refs: Iterable[RefBaseType],
) -> Iterable[RefBaseType]:
    buffer = set()
    for ref in refs:
        if not ref.id:
            continue
        key = (
            ref.id,
            ref.agency_id,
            ref.version,
            ref.maintainable_parent_id,
            ref.maintainable_parent_version,
        )
        if key not in buffer:
            yield ref
            buffer.add(key)


def extract_data_structure_ref(dataflow: DataflowType) -> RefBaseType | None:
    return (
        dataflow.structure.ref
        if dataflow.structure and dataflow.structure.ref
        else None
    )


def extract_data_structure_refs(
    dataflows: Sequence[DataflowType],
) -> Iterable[RefBaseType]:
    yield from unique_by_ref(
        ref for df in dataflows if (ref := extract_data_structure_ref(df)) is not None
    )


def extract_codelist_ref(component: ComponentType) -> RefBaseType | None:
    return (
        component.local_representation.enumeration.ref
        if component.local_representation and component.local_representation.enumeration
        else None
    )


def extract_concept_ref(component: ComponentType) -> RefBaseType | None:
    return component.concept_identity.ref if component.concept_identity else None


def extract_component_refs(
    reffunc: Callable[[ComponentType], RefBaseType | None],
    data_structures: Sequence[DataStructureType2],
) -> Iterable[RefBaseType]:
    def inner_extract_ref(
        component_list: Sequence[ComponentType],
    ) -> Iterable[RefBaseType]:
        yield from (ref for d in component_list if (ref := reffunc(d)) is not None)

    def inner_extract_refs(
        data_structure: DataStructureType2,
    ) -> Iterable[RefBaseType]:
        if data_structure.data_structure_components:
            if data_structure.data_structure_components.dimension_list:
                yield from inner_extract_ref(
                    data_structure.data_structure_components.dimension_list.time_dimension
                )
                yield from inner_extract_ref(
                    data_structure.data_structure_components.dimension_list.dimension
                )
            if data_structure.data_structure_components.attribute_list:
                yield from inner_extract_ref(
                    data_structure.data_structure_components.attribute_list.attribute
                )
            if (
                data_structure.data_structure_components.measure_list
                and data_structure.data_structure_components.measure_list.primary_measure
            ):
                yield from inner_extract_ref(
                    [
                        data_structure.data_structure_components.measure_list.primary_measure
                    ]
                )

    yield from unique_by_ref(
        cl for ds in data_structures for cl in inner_extract_refs(ds)
    )


extract_codelist_refs = partial(extract_component_refs, extract_codelist_ref)
extract_concept_refs = partial(extract_component_refs, extract_concept_ref)
