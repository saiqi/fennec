import pytest
from xsdata.models.datatype import XmlPeriod
from fennec_api.sdmx_v21.parser import (
    parse_structure,
    parse_data,
    Structure,
    GenericData,
    StructureSpecificData,
    Error,
)


def open_fixture(name: str) -> bytes:
    with open(f"data/sdmxml21/{name}.xml", "rb") as f:
        return f.read()


@pytest.mark.xfail
def test_parse_agencyschemes() -> None:
    message = parse_structure(open_fixture("agencyscheme"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.organisation_schemes
    agency_scheme = message.structures.organisation_schemes.agency_scheme[0]
    assert agency_scheme.id == "AGENCIES"
    assert agency_scheme.agency_id == "SDMX"
    assert agency_scheme.version == "1.0"
    assert (
        agency_scheme.urn
        == "urn:sdmx:org.sdmx.infomodel.base.AgencyScheme=SDMX:AGENCIES(1.0)"
    )
    assert agency_scheme.is_final is False


def test_parse_categoryschemes() -> None:
    message = parse_structure(open_fixture("categoryscheme"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.category_schemes
    category_scheme = message.structures.category_schemes.category_scheme[0]
    assert category_scheme.id == "CLASSEMENT_DATAFLOWS"
    assert category_scheme.agency_id == "FR1"
    assert category_scheme.version == "1.0"
    assert (
        category_scheme.urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.CategoryScheme=FR1:CLASSEMENT_DATAFLOWS(1.0)"
    )
    assert category_scheme.name[0].lang == "fr"
    assert category_scheme.name[0].value == "Classement des dataflows"
    assert category_scheme.category[0].id == "ECO"
    assert (
        category_scheme.category[0].urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.Category=FR1:CLASSEMENT_DATAFLOWS(1.0).ECO"
    )
    assert category_scheme.category[0].category[0].id == "COMMERCE_EXT"


def test_parse_categorisations() -> None:
    message = parse_structure(open_fixture("categorisation"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.categorisations
    categorisation = message.structures.categorisations.categorisation[0]
    assert categorisation.id == "COMMERCE_EXT_BALANCE-PAIEMENTS"
    assert categorisation.agency_id == "FR1"
    assert categorisation.version == "1.0"
    assert (
        categorisation.urn
        == "urn:sdmx:org.sdmx.infomodel.categoryscheme.Categorisation=FR1:COMMERCE_EXT_BALANCE-PAIEMENTS(1.0)"
    )
    assert categorisation.name[0].lang == "fr"
    assert (
        categorisation.name[0].value
        == "Association entre la catégorie COMMERCE_EXT et le dataflows BALANCE-PAIEMENTS"
    )
    assert categorisation.source
    assert categorisation.source.ref
    assert categorisation.source.ref.id == "BALANCE-PAIEMENTS"
    assert categorisation.source.ref.version == "1.0"
    assert categorisation.source.ref.agency_id == "FR1"
    assert categorisation.source.ref.package
    assert categorisation.source.ref.package.value == "datastructure"
    assert categorisation.source.ref.class_value
    assert categorisation.source.ref.class_value.value == "Dataflow"
    assert categorisation.target
    assert categorisation.target.ref
    assert categorisation.target.ref.id == "COMMERCE_EXT"
    assert categorisation.target.ref.maintainable_parent_id == "CLASSEMENT_DATAFLOWS"
    assert categorisation.target.ref.maintainable_parent_version == "1.0"
    assert categorisation.target.ref.agency_id == "FR1"
    assert categorisation.target.ref.package
    assert categorisation.target.ref.package.value == "categoryscheme"
    assert categorisation.target.ref.class_value
    assert categorisation.target.ref.class_value.value == "Category"


def test_parse_codelists() -> None:
    message = parse_structure(open_fixture("codelist"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.codelists
    codelist = message.structures.codelists.codelist[0]
    assert codelist.id == "CL_PERIODICITE"
    assert (
        codelist.urn
        == "urn:sdmx:org.sdmx.infomodel.codelist.Codelist=FR1:CL_PERIODICITE(1.0)"
    )
    assert codelist.agency_id == "FR1"
    assert codelist.version == "1.0"
    assert codelist.name[0].lang == "fr"
    assert codelist.name[0].value == "Périodicité"
    assert codelist.code[0].id == "M"
    assert (
        codelist.code[0].urn
        == "urn:sdmx:org.sdmx.infomodel.codelist.Code=FR1:CL_PERIODICITE(1.0).M"
    )
    assert codelist.code[0].name[0].lang == "fr"
    assert codelist.code[0].name[0].value == "Mensuelle"


def test_parse_conceptschemes() -> None:
    message = parse_structure(open_fixture("conceptscheme"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.concepts
    concept_scheme = message.structures.concepts.concept_scheme[0]
    assert concept_scheme.id == "CONCEPTS_INSEE"
    assert (
        concept_scheme.urn
        == "urn:sdmx:org.sdmx.infomodel.conceptscheme.ConceptScheme=FR1:CONCEPTS_INSEE(1.0)"
    )
    assert concept_scheme.agency_id == "FR1"
    assert concept_scheme.version == "1.0"
    assert concept_scheme.name[0].lang == "fr"
    assert concept_scheme.name[0].value == "Concepts Insee"
    assert concept_scheme.concept[0].id == "FREQ"
    assert (
        concept_scheme.concept[0].urn
        == "urn:sdmx:org.sdmx.infomodel.conceptscheme.Concept=FR1:CONCEPTS_INSEE(1.0).FREQ"
    )
    assert concept_scheme.concept[0].name[0].lang == "fr"
    assert concept_scheme.concept[0].name[0].value == "Périodicité"


def test_parse_contentconstraint() -> None:
    message = parse_structure(open_fixture("contentconstraint"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.constraints
    content_constraint = message.structures.constraints.content_constraint[0]
    assert (
        content_constraint.urn
        == "urn:sdmx:org.sdmx.infomodel.registry.ContentConstraint=ECB:AME_CONSTRAINTS(1.0)"
    )
    assert content_constraint.is_external_reference is False
    assert content_constraint.agency_id == "ECB"
    assert content_constraint.id == "AME_CONSTRAINTS"
    assert content_constraint.is_final is False
    assert content_constraint.type_value.value == "Allowed"
    assert content_constraint.version == "1.0"
    assert content_constraint.name[0].lang == "en"
    assert content_constraint.name[0].value == "Constraints for the AME dataflow."
    assert content_constraint.constraint_attachment
    assert content_constraint.constraint_attachment.dataflow[0].ref
    assert content_constraint.constraint_attachment.dataflow[0].ref.id == "AME"
    assert content_constraint.constraint_attachment.dataflow[0].ref.package
    assert (
        content_constraint.constraint_attachment.dataflow[0].ref.package.value
        == "datastructure"
    )
    assert content_constraint.constraint_attachment.dataflow[0].ref.agency_id == "ECB"
    assert content_constraint.constraint_attachment.dataflow[0].ref.version == "1.0"
    assert content_constraint.constraint_attachment.dataflow[0].ref.class_value
    assert (
        content_constraint.constraint_attachment.dataflow[0].ref.class_value.value
        == "Dataflow"
    )
    assert content_constraint.cube_region[0].include is True
    assert content_constraint.cube_region[0].key_value[0].id == "AME_ITEM"
    assert content_constraint.cube_region[0].key_value[0].value[0].value == "UDGGL"


def test_parse_dataflows() -> None:
    message = parse_structure(open_fixture("dataflow"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.dataflows
    dataflow = message.structures.dataflows.dataflow[0]
    assert dataflow.id == "BALANCE-PAIEMENTS"
    assert (
        dataflow.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.Dataflow=FR1:BALANCE-PAIEMENTS(1.0)"
    )
    assert dataflow.agency_id == "FR1"
    assert dataflow.version == "1.0"
    assert dataflow.structure
    assert dataflow.structure.ref
    assert dataflow.structure.ref.id == "BALANCE-PAIEMENTS"
    assert dataflow.structure.ref.agency_id == "FR1"
    assert dataflow.structure.ref.version == "1.0"
    assert dataflow.structure.ref.package
    assert dataflow.structure.ref.package.value == "datastructure"
    assert dataflow.structure.ref.class_value
    assert dataflow.structure.ref.class_value.value == "DataStructure"
    assert dataflow.name[0].lang == "fr"
    assert dataflow.name[0].value == "Balance des paiements"


def test_parse_datastructures() -> None:
    message = parse_structure(open_fixture("datastructure"))
    assert isinstance(message, Structure)
    assert message.structures
    assert message.structures.data_structures
    data_structure = message.structures.data_structures.data_structure[0]
    assert data_structure.id == "BALANCE-PAIEMENTS"
    assert data_structure.agency_id == "FR1"
    assert data_structure.version == "1.0"
    assert (
        data_structure.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.DataStructure=FR1:BALANCE-PAIEMENTS(1.0)"
    )
    assert data_structure.name[0].lang == "fr"
    assert data_structure.name[0].value == "Balance des paiements"
    assert data_structure.data_structure_components
    assert data_structure.data_structure_components.dimension_list
    time_dimension = (
        data_structure.data_structure_components.dimension_list.time_dimension[0]
    )
    assert time_dimension.id == "TIME_PERIOD"
    assert (
        time_dimension.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.TimeDimension=FR1:BALANCE-PAIEMENTS(1.0).TIME_PERIOD"
    )
    assert time_dimension.position == 1
    assert time_dimension.concept_identity
    assert time_dimension.concept_identity.ref
    assert time_dimension.concept_identity.ref.id == "TIME_PERIOD"
    assert (
        time_dimension.concept_identity.ref.maintainable_parent_id == "CONCEPTS_INSEE"
    )
    assert time_dimension.concept_identity.ref.maintainable_parent_version == "1.0"
    assert time_dimension.concept_identity.ref.agency_id == "FR1"
    assert time_dimension.concept_identity.ref.package
    assert time_dimension.concept_identity.ref.package.value == "conceptscheme"
    assert time_dimension.concept_identity.ref.class_value
    assert time_dimension.concept_identity.ref.class_value.value == "Concept"
    assert time_dimension.local_representation
    assert time_dimension.local_representation.text_format
    assert (
        time_dimension.local_representation.text_format.text_type.value
        == "ObservationalTimePeriod"
    )
    dimension = data_structure.data_structure_components.dimension_list.dimension[0]
    assert dimension.id == "FREQ"
    assert (
        dimension.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.Dimension=FR1:BALANCE-PAIEMENTS(1.0).FREQ"
    )
    assert dimension.position == 2
    assert dimension.concept_identity
    assert dimension.concept_identity.ref
    assert dimension.concept_identity.ref.id == "FREQ"
    assert dimension.concept_identity.ref.maintainable_parent_id == "CONCEPTS_INSEE"
    assert dimension.concept_identity.ref.maintainable_parent_version == "1.0"
    assert dimension.concept_identity.ref.agency_id == "FR1"
    assert dimension.concept_identity.ref.package
    assert dimension.concept_identity.ref.package.value == "conceptscheme"
    assert dimension.concept_identity.ref.class_value
    assert dimension.concept_identity.ref.class_value.value == "Concept"
    assert dimension.local_representation
    assert dimension.local_representation.enumeration
    assert dimension.local_representation.enumeration.ref
    assert dimension.local_representation.enumeration.ref.id == "CL_PERIODICITE"
    assert dimension.local_representation.enumeration.ref.agency_id == "FR1"
    assert dimension.local_representation.enumeration.ref.version == "1.0"
    assert dimension.local_representation.enumeration.ref.package
    assert dimension.local_representation.enumeration.ref.package.value == "codelist"
    assert dimension.local_representation.enumeration.ref.class_value
    assert (
        dimension.local_representation.enumeration.ref.class_value.value == "Codelist"
    )
    assert data_structure.data_structure_components.attribute_list
    attribute = data_structure.data_structure_components.attribute_list.attribute[0]
    assert attribute.id == "UNIT_MULT"
    assert (
        attribute.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.DataAttribute=FR1:BALANCE-PAIEMENTS(1.0).UNIT_MULT"
    )
    assert attribute.assignment_status
    assert attribute.assignment_status.value == "Mandatory"
    assert attribute.concept_identity
    assert attribute.concept_identity.ref
    assert attribute.concept_identity.ref.id == "UNIT_MULT"
    assert attribute.concept_identity.ref.maintainable_parent_id == "CONCEPTS_INSEE"
    assert attribute.concept_identity.ref.maintainable_parent_version == "1.0"
    assert attribute.concept_identity.ref.agency_id == "FR1"
    assert attribute.concept_identity.ref.package
    assert attribute.concept_identity.ref.package.value == "conceptscheme"
    assert attribute.concept_identity.ref.class_value
    assert attribute.concept_identity.ref.class_value.value == "Concept"
    assert attribute.attribute_relationship
    assert attribute.attribute_relationship.dimension[0].ref
    assert attribute.attribute_relationship.dimension[0].ref.id == "FREQ"
    assert data_structure.data_structure_components.measure_list
    assert data_structure.data_structure_components.measure_list.primary_measure
    primary_measure = (
        data_structure.data_structure_components.measure_list.primary_measure
    )
    assert primary_measure.id == "OBS_VALUE"
    assert (
        primary_measure.urn
        == "urn:sdmx:org.sdmx.infomodel.datastructure.PrimaryMeasure=FR1:BALANCE-PAIEMENTS(1.0).OBS_VALUE"
    )
    assert primary_measure.concept_identity
    assert primary_measure.concept_identity.ref
    assert primary_measure.concept_identity.ref.id == "OBS_VALUE"
    assert (
        primary_measure.concept_identity.ref.maintainable_parent_id == "CONCEPTS_INSEE"
    )
    assert primary_measure.concept_identity.ref.maintainable_parent_version == "1.0"
    assert primary_measure.concept_identity.ref.agency_id == "FR1"
    assert primary_measure.concept_identity.ref.package
    assert primary_measure.concept_identity.ref.package.value == "conceptscheme"
    assert primary_measure.concept_identity.ref.class_value
    assert primary_measure.concept_identity.ref.class_value.value == "Concept"


def test_parse_errors() -> None:
    message = parse_structure(open_fixture("error"))
    assert isinstance(message, Error)
    error_message = message.error_message[0]
    assert error_message.code
    assert error_message.code == "140"
    assert error_message.text[0].value == "La syntaxe de la requete est invalide."


def test_parse_genericdata() -> None:
    message = parse_data(open_fixture("genericdata"))
    assert isinstance(message, GenericData)
    assert message.data_set[0].structure_ref == "FR1_BALANCE-PAIEMENTS_1_0"
    serie = message.data_set[0].series[0]
    assert serie.series_key
    assert serie.series_key.value[0].id == "BASIND"
    assert serie.series_key.value[0].value == "SO"
    assert serie.attributes
    assert serie.attributes.value[0].id == "IDBANK"
    assert serie.attributes.value[0].value == "001694087"
    assert serie.obs[0].obs_dimension
    assert serie.obs[0].obs_dimension.value == "2022-11"
    assert serie.obs[0].obs_value
    assert serie.obs[0].obs_value.value == "203"
    assert serie.obs[0].attributes
    assert serie.obs[0].attributes.value[0].id == "OBS_STATUS"
    assert serie.obs[0].attributes.value[0].value == "A"


def test_parse_structurespecificdata() -> None:
    message = parse_data(open_fixture("structurespecificdata"))
    assert isinstance(message, StructureSpecificData)
    assert message.data_set[0].structure_ref == "FR1_BALANCE-PAIEMENTS_1_0"
    serie = message.data_set[0].series[0]
    assert serie.local_attributes == dict(
        BASIND="SO",
        CORRECTION="BRUT",
        COMPTE="CREDITS",
        FREQ="M",
        UNIT_MULT="6",
        INDICATEUR="BALANCE_DES_PAIEMENTS",
        UNIT_MEASURE="EUROS",
        NATURE="VALEUR_ABSOLUE",
        REF_AREA="FE",
        INSTRUMENTS_BALANCE_PAIEMENTS="181",
        IDBANK="001694087",
        TITLE_FR="Balance des paiements - Crédit - Transactions courantes - Revenus primaires - Revenus des investissements - Revenus des avoirs de réserve - Données brutes",
        TITLE_EN="Balance of payments - Credit - Current transactions - Primary income - Investment income - Reserve assets - Raw data",
        LAST_UPDATE="2023-01-09",
        DECIMALS="0",
    )
    assert serie.obs[0].local_attributes == dict(
        OBS_STATUS="A",
        OBS_QUAL="DEF",
        OBS_TYPE="A",
    )
    assert serie.obs[0].obs_value
    assert serie.obs[0].obs_value == "203"
    assert serie.obs[0].time_period == XmlPeriod("2022-11")
