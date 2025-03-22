from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, func, ForeignKey
from fennec_auth.database import Base


class Group(Base):
    __tablename__ = "group"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ClientApplication(Base):
    __tablename__ = "client_application"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    client_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    client_secret_hash: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=True)
    groups: Mapped[Group] = relationship(lazy="selectin")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="client_application_permission",
        viewonly=True,
        lazy="selectin",
    )


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    role: Mapped[str] = mapped_column(String(5), nullable=False)
    client_application_id: Mapped[int] = mapped_column(
        ForeignKey("client_application.id"), nullable=False
    )
    client_application: Mapped[ClientApplication] = relationship(lazy="selectin")


class ClientApplicationPermission(Base):
    __tablename__ = "client_application_permission"
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permission.id"), primary_key=True
    )
    client_application_id: Mapped[int] = mapped_column(
        ForeignKey("client_application.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class UserPermission(Base):
    __tablename__ = "user_permission"
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permission.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(5), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    has_temporary_password: Mapped[bool] = mapped_column(Boolean, default=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=True)
    groups: Mapped[Group | None] = relationship(lazy="selectin")
    permissions: Mapped[list[Permission]] = relationship(
        secondary="user_permission",
        lazy="selectin",
        viewonly=True,
    )


__all__ = [
    "Base",
    "Group",
    "User",
    "ClientApplication",
    "Permission",
    "UserPermission",
    "ClientApplicationPermission",
]
