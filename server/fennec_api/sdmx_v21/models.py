from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func, Boolean, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fennec_api.core.database import Base


class Provider(Base):
    __tablename__ = "sdmxv21_provider"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    agency_id: Mapped[str] = mapped_column(String, nullable=False)
    root_url: Mapped[str] = mapped_column(String, nullable=False)
    bulk_download: Mapped[bool] = mapped_column(Boolean, nullable=False)
    skip_categories: Mapped[bool] = mapped_column(Boolean, nullable=False)
    process_all_agencies: Mapped[bool] = mapped_column(Boolean, nullable=False)


class IdentifiableMixin:
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    agency_id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    version: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)


class LabelizableMixin:
    name: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)


class DataStructure(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_datastructure"
    time_dimensions: Mapped[list["TimeDimension"]] = relationship(
        back_populates="data_structure", lazy="selectin"
    )
    dimensions: Mapped[list["Dimension"]] = relationship(
        back_populates="data_structure", lazy="selectin"
    )
    attributes: Mapped[list["Attribute"]] = relationship(
        back_populates="data_structure", lazy="selectin"
    )
    primary_measures: Mapped[list["PrimaryMeasure"]] = relationship(
        back_populates="data_structure", lazy="selectin"
    )


class DataStructureComponent:
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)
    data_structure_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    data_structure_agency_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    data_structure_version: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    concept_id: Mapped[str | None] = mapped_column(String, nullable=True)
    concept_maintainable_parent_id: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    concept_maintainable_parent_version: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    concept_agency_id: Mapped[str | None] = mapped_column(String, nullable=True)
    concept_package: Mapped[str | None] = mapped_column(String, nullable=True)
    concept_class: Mapped[str | None] = mapped_column(String, nullable=True)


class RepresentableComponent:
    format_type: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_id: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_agency_id: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_version: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_package: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_class: Mapped[str | None] = mapped_column(String, nullable=True)


class TimeDimension(Base, DataStructureComponent, RepresentableComponent):
    __tablename__ = "sdmxv21_timedimension"
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    data_structure: Mapped[DataStructure] = relationship(
        back_populates="time_dimensions"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_structure_id", "data_structure_agency_id", "data_structure_version"],
            [DataStructure.id, DataStructure.agency_id, DataStructure.version],
        ),
    )


class Dimension(Base, DataStructureComponent, RepresentableComponent):
    __tablename__ = "sdmxv21_dimension"
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    data_structure: Mapped[DataStructure] = relationship(back_populates="dimensions")

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_structure_id", "data_structure_agency_id", "data_structure_version"],
            [DataStructure.id, DataStructure.agency_id, DataStructure.version],
        ),
    )


class Attribute(Base, DataStructureComponent, RepresentableComponent):
    __tablename__ = "sdmxv21_attribute"
    assignment_status: Mapped[str | None] = mapped_column(String, nullable=True)

    data_structure: Mapped[DataStructure] = relationship(back_populates="attributes")

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_structure_id", "data_structure_agency_id", "data_structure_version"],
            [DataStructure.id, DataStructure.agency_id, DataStructure.version],
        ),
    )


class PrimaryMeasure(Base, DataStructureComponent):
    __tablename__ = "sdmxv21_primary_measure"

    data_structure: Mapped[DataStructure] = relationship(
        back_populates="primary_measures"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_structure_id", "data_structure_agency_id", "data_structure_version"],
            [DataStructure.id, DataStructure.agency_id, DataStructure.version],
        ),
    )


class Dataflow(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_dataflow"
    structure_id: Mapped[str | None] = mapped_column(String, nullable=True)
    structure_agency_id: Mapped[str | None] = mapped_column(String, nullable=True)
    structure_version: Mapped[str | None] = mapped_column(String, nullable=True)
    structure_package: Mapped[str | None] = mapped_column(String, nullable=True)
    structure_class: Mapped[str | None] = mapped_column(String, nullable=True)


class CategoryScheme(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_categoryscheme"

    categories: Mapped[list["Category"]] = relationship(
        back_populates="category_scheme",
        lazy="selectin",
        primaryjoin="""and_(
            CategoryScheme.id == Category.category_scheme_id,
            CategoryScheme.agency_id == Category.category_scheme_agency_id,
            CategoryScheme.version == Category.category_scheme_version,
            Category.parent_id.is_(None),
        )""",
    )


class Category(Base, LabelizableMixin):
    __tablename__ = "sdmxv21_category"
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)
    category_scheme_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    category_scheme_agency_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    category_scheme_version: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    category_scheme: Mapped[CategoryScheme] = relationship(back_populates="categories")

    parent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_scheme_id: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_scheme_agency_id: Mapped[str | None] = mapped_column(String, nullable=True)
    parent_scheme_version: Mapped[str | None] = mapped_column(String, nullable=True)

    children: Mapped[list["Category"]] = relationship("Category")

    __table_args__ = (
        ForeignKeyConstraint(
            [category_scheme_id, category_scheme_agency_id, category_scheme_version],
            [CategoryScheme.id, CategoryScheme.agency_id, CategoryScheme.version],
        ),
        ForeignKeyConstraint(
            [
                parent_id,
                parent_scheme_id,
                parent_scheme_agency_id,
                parent_scheme_version,
            ],
            [
                "sdmxv21_category.id",
                "sdmxv21_category.category_scheme_id",
                "sdmxv21_category.category_scheme_agency_id",
                "sdmxv21_category.category_scheme_version",
            ],
        ),
    )


class Codelist(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_codelist"

    codes: Mapped[list["Code"]] = relationship(
        back_populates="codelist", lazy="selectin"
    )


class Code(Base, LabelizableMixin):
    __tablename__ = "sdmxv21_code"
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)
    codelist_id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    codelist_agency_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    codelist_version: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    codelist: Mapped[Codelist] = relationship(back_populates="codes")

    __table_args__ = (
        ForeignKeyConstraint(
            [codelist_id, codelist_agency_id, codelist_version],
            [Codelist.id, Codelist.agency_id, Codelist.version],
        ),
    )


class ConceptScheme(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_conceptscheme"

    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="concept_scheme", lazy="selectin"
    )


class Concept(Base, LabelizableMixin):
    __tablename__ = "sdmxv21_concept"
    id: Mapped[str] = mapped_column(String, nullable=False, primary_key=True)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)
    concept_scheme_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    concept_scheme_agency_id: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    concept_scheme_version: Mapped[str] = mapped_column(
        String, nullable=False, primary_key=True
    )
    concept_scheme: Mapped[ConceptScheme] = relationship(back_populates="concepts")

    __table_args__ = (
        ForeignKeyConstraint(
            [concept_scheme_id, concept_scheme_agency_id, concept_scheme_version],
            [ConceptScheme.id, ConceptScheme.agency_id, ConceptScheme.version],
        ),
    )


class Categorisation(Base, IdentifiableMixin, LabelizableMixin):
    __tablename__ = "sdmxv21_categorisation"
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    source_agency_id: Mapped[str] = mapped_column(String, nullable=False)
    source_version: Mapped[str] = mapped_column(String, nullable=False)
    source_package: Mapped[str] = mapped_column(String, nullable=False)
    source_class: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[str] = mapped_column(String, nullable=False)
    maintainable_parent_id: Mapped[str] = mapped_column(String, nullable=False)
    maintainable_parent_version: Mapped[str] = mapped_column(String, nullable=False)
    target_agency_id: Mapped[str] = mapped_column(String, nullable=False)
    target_package: Mapped[str] = mapped_column(String, nullable=False)
    target_class: Mapped[str] = mapped_column(String, nullable=False)
