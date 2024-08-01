from typing import AsyncGenerator
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
import fennec_api.sdmx_v21.etl.extract as extract
import fennec_api.sdmx_v21.etl.load as load
from fennec_api.sdmx_v21.parser import parse_structure
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
    dataflows = await extract.fetch_all_dataflows(client=mock_sdmx_client)
    await extract.fetch_all_categorisations(client=mock_sdmx_client)
    await extract.fetch_all_category_schemes(client=mock_sdmx_client)

    dataflow = dataflows[0]
    data_structure = await extract.fetch_data_structure(
        client=mock_sdmx_client, dataflow=dataflow
    )

    await extract.fetch_codelists(
        client=mock_sdmx_client, data_structure=data_structure
    )
    await extract.fetch_concept_schemes(
        client=mock_sdmx_client, data_structure=data_structure
    )


@pytest.mark.asyncio
async def test_load_dataflows(session: AsyncSession) -> None:
    with open("data/sdmxml21/dataflow.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.dataflows
        dataflows = msg.structures.dataflows.dataflow

    await load.load_dataflows(session, dataflows)
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
async def test_load_data_structure(session: AsyncSession) -> None:
    with open("data/sdmxml21/datastructure.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.data_structures
        data_structure = msg.structures.data_structures.data_structure

    await load.load_data_structure(session, data_structure)

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
async def test_load_category_schemes(session: AsyncSession) -> None:
    with open("data/sdmxml21/categoryscheme.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.category_schemes
        category_schemes = msg.structures.category_schemes.category_scheme

    await load.load_category_schemes(session, category_schemes)

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
async def test_load_codelists(session: AsyncSession) -> None:
    with open("data/sdmxml21/codelist.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.codelists
        codelists = msg.structures.codelists.codelist

    await load.load_codelists(session, codelists)

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
async def test_load_concept_schemes(session: AsyncSession) -> None:
    with open("data/sdmxml21/conceptscheme.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.concepts
        concept_scheme = msg.structures.concepts.concept_scheme

    await load.load_concept_schemes(session, concept_scheme)

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
async def test_load_categorisations(session: AsyncSession) -> None:
    with open("data/sdmxml21/categorisation.xml", "rb") as f:
        msg = parse_structure(f.read())
        assert isinstance(msg, Structure)
        assert msg.structures
        assert msg.structures.categorisations
        categorisations = msg.structures.categorisations.categorisation

    await load.load_categorisations(session, categorisations)

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
