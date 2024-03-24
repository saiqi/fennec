from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from fennec_api.core.database import Base


class IdentifiableMixin:
    id: Mapped[str] = mapped_column(String, nullable=False)
    urn: Mapped[str | None] = mapped_column(String, nullable=True)
    agency_id: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SDMX21Dataflow(Base, IdentifiableMixin, TimestampMixin):
    __tablename__ = "sdmx21_dataflow"
    uid: Mapped[int] = mapped_column(Integer, primary_key=True)
    names: Mapped[list["SDMX21DataflowName"]] = relationship(back_populates="dataflow")


class SDMX21DataflowName(Base):
    __tablename__ = "sdmx21_dataflow_name"
    uid: Mapped[int] = mapped_column(Integer, primary_key=True)
    lang: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String)
    dataflow_uid: Mapped[int] = mapped_column(ForeignKey("sdmx21_dataflow.uid"))
    dataflow: Mapped[SDMX21Dataflow] = relationship(back_populates="names")


class SDMX21DataflowDescription(Base):
    __tablename__ = "sdmx21_dataflow_description"
    uid: Mapped[int] = mapped_column(Integer, primary_key=True)
    lang: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[str] = mapped_column(String)
    dataflow_uid: Mapped[int] = mapped_column(ForeignKey("sdmx21_dataflow.uid"))
    dataflow: Mapped[SDMX21Dataflow] = relationship(back_populates="names")
