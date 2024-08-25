from typing import AsyncGenerator, Sequence
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import aiofiles
import httpx
from fennec_api.sdmx_v21.client import (
    SDMX21RestClient,
)
import fennec_api.sdmx_v21.etl as etl
from fennec_api.sdmx_v21.parser import (
    parse_structure,
    DataflowType,
    DataStructureType2,
    CategorySchemeType,
    CategorisationType,
    CodelistType,
    ConceptSchemeType,
)
from fennec_api.sdmx_v21.parser import Structure
from fennec_api.sdmx_v21.models import (
    Dataflow,
    DataStructure,
    CategoryScheme,
    Category,
    Codelist,
    ConceptScheme,
    Categorisation,
)


async def open_fixture(path: str) -> bytes:
    async with aiofiles.open(path, "rb") as f:
        content: bytes = await f.read()
        return content


@pytest_asyncio.fixture()
async def categorisation_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/categorisation.xml")


@pytest_asyncio.fixture()
async def categorisations(
    categorisation_data: bytes,
) -> AsyncGenerator[Sequence[CategorisationType], None]:
    msg = parse_structure(categorisation_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.categorisations
    yield msg.structures.categorisations.categorisation


@pytest_asyncio.fixture()
async def category_scheme_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/categoryscheme.xml")


@pytest_asyncio.fixture()
async def category_schemes(
    category_scheme_data: bytes,
) -> AsyncGenerator[Sequence[CategorySchemeType], None]:
    msg = parse_structure(category_scheme_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.category_schemes
    yield msg.structures.category_schemes.category_scheme


@pytest_asyncio.fixture()
async def codelist_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/codelist.xml")


@pytest_asyncio.fixture()
async def codelists(
    codelist_data: bytes,
) -> AsyncGenerator[Sequence[CodelistType], None]:
    msg = parse_structure(codelist_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.codelists
    yield msg.structures.codelists.codelist


@pytest_asyncio.fixture()
async def concept_scheme_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/conceptscheme.xml")


@pytest_asyncio.fixture()
async def concept_schemes(
    concept_scheme_data: bytes,
) -> AsyncGenerator[Sequence[ConceptSchemeType], None]:
    msg = parse_structure(concept_scheme_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.concepts
    yield msg.structures.concepts.concept_scheme


@pytest_asyncio.fixture()
async def content_constraint_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/contentconstraint.xml")


@pytest_asyncio.fixture()
async def dataflow_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/dataflow.xml")


@pytest_asyncio.fixture()
async def dataflows(
    dataflow_data: bytes,
) -> AsyncGenerator[Sequence[DataflowType], None]:
    msg = parse_structure(dataflow_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.dataflows
    yield msg.structures.dataflows.dataflow


@pytest_asyncio.fixture()
async def data_structure_data() -> AsyncGenerator[bytes, None]:
    yield await open_fixture("data/sdmxml21/datastructure.xml")


@pytest_asyncio.fixture()
async def data_structure(
    data_structure_data: bytes,
) -> AsyncGenerator[Sequence[DataStructureType2], None]:
    msg = parse_structure(data_structure_data)
    assert isinstance(msg, Structure)
    assert msg.structures
    assert msg.structures.data_structures
    yield msg.structures.data_structures.data_structure


@pytest_asyncio.fixture()
async def mock_http_client(
    categorisation_data: bytes,
    category_scheme_data: bytes,
    codelist_data: bytes,
    concept_scheme_data: bytes,
    content_constraint_data: bytes,
    dataflow_data: bytes,
    data_structure_data: bytes,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async def open_fixture(req: httpx.Request) -> httpx.Response:
        if "categorisation" in req.url.path:
            content = categorisation_data
        elif "categoryscheme" in req.url.path:
            content = category_scheme_data
        elif "codelist" in req.url.path:
            content = codelist_data
        elif "conceptscheme" in req.url.path:
            content = concept_scheme_data
        elif "contentconstraint" in req.url.path:
            content = content_constraint_data
        elif "dataflow" in req.url.path:
            content = dataflow_data
        elif "datastructure" in req.url.path:
            content = data_structure_data
        else:
            raise NotImplementedError

        return httpx.Response(200, content=content)

    async with httpx.AsyncClient(transport=httpx.MockTransport(open_fixture)) as client:
        yield client


@pytest_asyncio.fixture()
async def mock_sdmx_client(
    mock_http_client: httpx.AsyncClient,
) -> AsyncGenerator[SDMX21RestClient, None]:
    yield SDMX21RestClient(http_client=mock_http_client, root_url="http://test")


@pytest.mark.asyncio
async def test_crawl_structure(mock_sdmx_client: SDMX21RestClient) -> None:
    dataflows = await etl.fetch_all_dataflows(mock_sdmx_client)
    assert dataflows[0].id == "BALANCE-PAIEMENTS"

    categorisations = await etl.fetch_all_categorisations(mock_sdmx_client)
    assert categorisations[0].id == "COMMERCE_EXT_BALANCE-PAIEMENTS"

    category_schemes = await etl.fetch_all_category_schemes(mock_sdmx_client)
    assert category_schemes[0].id == "CLASSEMENT_DATAFLOWS"

    data_structures = [
        await etl.fetch_data_structure(mock_sdmx_client, ref)
        for ref in etl.extract_data_structure_refs(dataflows)
    ]
    assert data_structures[0].id == "BALANCE-PAIEMENTS"

    codelist_refs = list(etl.extract_codelist_refs(data_structures))
    concept_scheme_refs = list(etl.extract_concept_refs(data_structures))

    codelists = await etl.fetch_codelists(mock_sdmx_client, codelist_refs)
    assert codelists[0].id == "CL_PERIODICITE"

    concept_schemes = await etl.fetch_concept_schemes(
        mock_sdmx_client, concept_scheme_refs
    )
    assert concept_schemes[0].id == "CONCEPTS_INSEE"


@pytest.mark.asyncio
async def test_load_dataflows(
    session: AsyncSession, dataflows: Sequence[DataflowType]
) -> None:
    await etl.load_dataflows(session, dataflows)
    result_insert = await session.execute(
        select(Dataflow).filter(
            Dataflow.id == "BALANCE-PAIEMENTS",
            Dataflow.agency_id == "FR1",
            Dataflow.version == "1.0",
        )
    )
    inserted_dataflows = result_insert.scalars().all()
    assert len(inserted_dataflows) == 1
    assert (
        inserted_dataflows[0].urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.Dataflow=FR1:BALANCE-PAIEMENTS(1.0)"
    )
    assert inserted_dataflows[0].name == "Balance of payments"
    assert inserted_dataflows[0].description is None
    assert inserted_dataflows[0].structure_id == "BALANCE-PAIEMENTS"
    assert inserted_dataflows[0].structure_agency_id == "FR1"
    assert inserted_dataflows[0].structure_version == "1.0"
    assert inserted_dataflows[0].structure_package == "datastructure"
    assert inserted_dataflows[0].structure_class == "DataStructure"

    assert dataflows[0].structure
    assert dataflows[0].structure.ref
    dataflows[0].structure.ref.id = "DSD-BALANCE-PAIEMENTS"


@pytest.mark.asyncio
async def test_load_data_structure(
    session: AsyncSession, data_structure: Sequence[DataStructureType2]
) -> None:
    await etl.load_data_structures(session, data_structure)

    inserted_result = await session.execute(
        select(DataStructure).filter(
            DataStructure.id == "BALANCE-PAIEMENTS",
            DataStructure.agency_id == "FR1",
            DataStructure.version == "1.0",
        )
    )
    inserted_data_structure = inserted_result.scalars().all()
    assert len(inserted_data_structure) == 1
    assert inserted_data_structure[0].id == "BALANCE-PAIEMENTS"
    assert inserted_data_structure[0].agency_id == "FR1"
    assert inserted_data_structure[0].version == "1.0"
    assert (
        inserted_data_structure[0].urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=FR1:BALANCE-PAIEMENTS(1.0)"
    )
    assert inserted_data_structure[0].name == "Balance of payments"
    assert inserted_data_structure[0].description is None
    assert len(inserted_data_structure[0].time_dimensions) == 1
    assert len(inserted_data_structure[0].dimensions) == 9
    assert len(inserted_data_structure[0].attributes) == 12
    assert len(inserted_data_structure[0].primary_measures) == 1

    time_dimension = inserted_data_structure[0].time_dimensions[0]
    assert time_dimension.id == "TIME_PERIOD"
    assert (
        time_dimension.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.TimeDimension=FR1:BALANCE-PAIEMENTS(1.0).TIME_PERIOD"
    )
    assert time_dimension.position == 1
    assert time_dimension.concept_id == "TIME_PERIOD"
    assert time_dimension.concept_maintainable_parent_id == "CONCEPTS_INSEE"
    assert time_dimension.concept_maintainable_parent_version == "1.0"
    assert time_dimension.concept_agency_id == "FR1"
    assert time_dimension.concept_package == "conceptscheme"
    assert time_dimension.concept_class == "Concept"
    assert time_dimension.format_type == "ObservationalTimePeriod"

    dimension = inserted_data_structure[0].dimensions[0]
    assert dimension.id == "FREQ"
    assert (
        dimension.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.Dimension=FR1:BALANCE-PAIEMENTS(1.0).FREQ"
    )
    assert dimension.position == 2
    assert dimension.concept_id == "FREQ"
    assert dimension.concept_maintainable_parent_id == "CONCEPTS_INSEE"
    assert dimension.concept_maintainable_parent_version == "1.0"
    assert dimension.concept_agency_id == "FR1"
    assert dimension.concept_package == "conceptscheme"
    assert dimension.concept_class == "Concept"
    assert dimension.codelist_id == "CL_PERIODICITE"
    assert dimension.codelist_agency_id == "FR1"
    assert dimension.codelist_version == "1.0"
    assert dimension.codelist_package == "codelist"
    assert dimension.codelist_class == "Codelist"

    attribute = inserted_data_structure[0].attributes[0]
    assert attribute.id == "UNIT_MULT"
    assert (
        attribute.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.DataAttribute=FR1:BALANCE-PAIEMENTS(1.0).UNIT_MULT"
    )
    assert attribute.assignment_status == "Mandatory"
    assert attribute.concept_id == "UNIT_MULT"
    assert attribute.concept_maintainable_parent_id == "CONCEPTS_INSEE"
    assert attribute.concept_maintainable_parent_version == "1.0"
    assert attribute.concept_agency_id == "FR1"
    assert attribute.concept_package == "conceptscheme"
    assert attribute.concept_class == "Concept"
    assert attribute.format_type == "Integer"

    primary_measure = inserted_data_structure[0].primary_measures[0]
    assert primary_measure.id == "OBS_VALUE"
    assert (
        primary_measure.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.PrimaryMeasure=FR1:BALANCE-PAIEMENTS(1.0).OBS_VALUE"
    )
    assert primary_measure.concept_id == "OBS_VALUE"
    assert primary_measure.concept_maintainable_parent_id == "CONCEPTS_INSEE"
    assert primary_measure.concept_maintainable_parent_version == "1.0"
    assert primary_measure.concept_agency_id == "FR1"
    assert primary_measure.concept_package == "conceptscheme"
    assert primary_measure.concept_class == "Concept"


@pytest.mark.asyncio
async def test_load_category_schemes(
    session: AsyncSession, category_schemes: Sequence[CategorySchemeType]
) -> None:
    await etl.load_category_schemes(session, category_schemes)

    inserted_result = await session.execute(
        select(CategoryScheme)
        .filter(
            CategoryScheme.id == "CLASSEMENT_DATAFLOWS",
            CategoryScheme.agency_id == "FR1",
            CategoryScheme.version == "1.0",
        )
        .options(
            selectinload(CategoryScheme.categories).subqueryload(Category.children)
        )
    )
    inserted_category_scheme = inserted_result.scalars().all()

    assert len(inserted_category_scheme) == 1
    assert inserted_category_scheme[0].name == "Dataflows categorisation"
    assert inserted_category_scheme[0].description is None

    categories = inserted_category_scheme[0].categories
    assert len(categories) == 1
    assert categories[0].id == "ECO"
    assert (
        categories[0].urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.Category=FR1:CLASSEMENT_DATAFLOWS(1.0).ECO"
    )
    assert categories[0].name == "Economy – Economic outlook – National accounts"
    assert categories[0].description is None
    assert categories[0].parent_id is None
    assert categories[0].parent_scheme_id is None
    assert categories[0].parent_scheme_agency_id is None
    assert categories[0].parent_scheme_version is None

    assert len(categories[0].children) == 1
    assert categories[0].children[0].id == "COMMERCE_EXT"
    assert (
        categories[0].children[0].urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.Category=FR1:CLASSEMENT_DATAFLOWS(1.0).ECO.COMMERCE_EXT"
    )
    assert categories[0].children[0].name == "Foreign trade"
    assert categories[0].children[0].description is None
    assert categories[0].children[0].parent_id == "ECO"
    assert categories[0].children[0].parent_scheme_id == "CLASSEMENT_DATAFLOWS"
    assert categories[0].children[0].parent_scheme_agency_id == "FR1"
    assert categories[0].children[0].parent_scheme_version == "1.0"


@pytest.mark.asyncio
async def test_load_codelists(
    session: AsyncSession, codelists: Sequence[CodelistType]
) -> None:
    await etl.load_codelists(session, codelists)

    inserted_result = await session.execute(
        select(Codelist).filter(
            Codelist.id == "CL_PERIODICITE",
            Codelist.agency_id == "FR1",
            Codelist.version == "1.0",
        )
    )
    inserted_codelists = inserted_result.scalars().all()
    assert len(inserted_codelists) == 1
    assert (
        inserted_codelists[0].urn
        == "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=FR1:CL_PERIODICITE(1.0)"
    )
    assert inserted_codelists[0].name == "Frequency"
    assert inserted_codelists[0].description is None

    codes = inserted_codelists[0].codes
    assert len(codes) == 1
    assert codes[0].id == "M"
    assert (
        codes[0].urn
        == "urn:sdmx:org.sdmx.infomodel.codelist.Code=FR1:CL_PERIODICITE(1.0).M"
    )
    assert codes[0].name == "Monthly"
    assert codes[0].description is None


@pytest.mark.asyncio
async def test_load_concept_schemes(
    session: AsyncSession, concept_schemes: Sequence[ConceptSchemeType]
) -> None:
    await etl.load_concept_schemes(session, concept_schemes)

    inserted_result = await session.execute(
        select(ConceptScheme).filter(
            ConceptScheme.id == "CONCEPTS_INSEE",
            ConceptScheme.agency_id == "FR1",
            ConceptScheme.version == "1.0",
        )
    )
    inserted_concept_schemes = inserted_result.scalars().all()
    assert len(inserted_concept_schemes) == 1
    assert (
        inserted_concept_schemes[0].urn
        == "urn:sdmx:org.sdmx.infomodel.conceptscheme.ConceptScheme=FR1:CONCEPTS_INSEE(1.0)"
    )
    assert inserted_concept_schemes[0].name == "Insee concepts"
    assert inserted_concept_schemes[0].description is None

    concepts = inserted_concept_schemes[0].concepts
    assert len(concepts) == 10
    assert concepts[0].id == "FREQ"
    assert (
        concepts[0].urn
        == "urn:sdmx:org.sdmx.infomodel.conceptscheme.Concept=FR1:CONCEPTS_INSEE(1.0).FREQ"
    )
    assert concepts[0].name == "Frequency"
    assert concepts[0].description is None


@pytest.mark.asyncio
async def test_load_categorisations(
    session: AsyncSession, categorisations: Sequence[CategorisationType]
) -> None:
    await etl.load_categorisations(session, categorisations)

    inserted_result = await session.execute(
        select(Categorisation).filter(
            Categorisation.id == "COMMERCE_EXT_BALANCE-PAIEMENTS",
            Categorisation.agency_id == "FR1",
            Categorisation.version == "1.0",
        )
    )
    inserted_categorisations = inserted_result.scalars().all()
    assert len(inserted_categorisations) == 1
    assert (
        inserted_categorisations[0].urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.Categorisation=FR1:COMMERCE_EXT_BALANCE-PAIEMENTS(1.0)"
    )
    assert (
        inserted_categorisations[0].name
        == "Association between category COMMERCE_EXT and dataflows BALANCE-PAIEMENTS"
    )
    assert inserted_categorisations[0].description is None
    assert inserted_categorisations[0].source_id == "BALANCE-PAIEMENTS"
    assert inserted_categorisations[0].source_agency_id == "FR1"
    assert inserted_categorisations[0].source_version == "1.0"
    assert inserted_categorisations[0].source_package == "datastructure"
    assert inserted_categorisations[0].source_class == "Dataflow"
    assert inserted_categorisations[0].target_id == "COMMERCE_EXT"
    assert inserted_categorisations[0].maintainable_parent_id == "CLASSEMENT_DATAFLOWS"
    assert inserted_categorisations[0].maintainable_parent_version == "1.0"
    assert inserted_categorisations[0].target_agency_id == "FR1"
    assert inserted_categorisations[0].target_package == "categoryscheme"
    assert inserted_categorisations[0].target_class == "Category"


@pytest.mark.asyncio
async def test_extract_data_structure_refs(dataflows: Sequence[DataflowType]) -> None:
    dup_dataflows = [d for d in dataflows] + [d for d in dataflows]
    unique_refs = list(etl.extract_data_structure_refs(dup_dataflows))
    assert len(unique_refs) == 1


@pytest.mark.asyncio
async def test_extract_codelist_refs(
    data_structure: Sequence[DataStructureType2],
) -> None:
    dup_dsds = [d for d in data_structure] + [d for d in data_structure]
    unique_refs = list(etl.extract_codelist_refs(dup_dsds))
    assert len(unique_refs) == 14


@pytest.mark.asyncio
async def test_extract_concept_scheme_refs(
    data_structure: Sequence[DataStructureType2],
) -> None:
    dup_dsds = [d for d in data_structure] + [d for d in data_structure]
    unique_refs = list(etl.extract_concept_refs(dup_dsds))
    assert len(unique_refs) == 23
