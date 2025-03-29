from typing import Annotated, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

allowed_roles = ["read", "write", "admin"]
RoleType = Annotated[str, Literal[tuple(allowed_roles)]]

allowed_client_types = ["user", "service"]
ClientType = Annotated[str, Literal[tuple(allowed_client_types)]]


class PasswordUpdate(BaseModel):
    password: str


class RoleUpdate(BaseModel):
    role: RoleType


class ActiveStatusUpdate(BaseModel):
    is_active: bool


class ExternalStatusUpdate(BaseModel):
    is_external: bool


class GroupUpdate(BaseModel):
    name: str


class PermissionUpdate(BaseModel):
    client_application: str
    role: RoleType


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupOut(GroupBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    first_name: str
    last_name: str
    user_name: str
    email: EmailStr
    role: RoleType


class UserCreate(UserBase):
    pass


class UserOut(UserBase):
    id: int
    is_active: bool
    has_temporary_password: bool
    is_external: bool
    groups: GroupOut | None

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    id: int
    is_active: bool
    groups: GroupOut | None


class ClientApplicationBase(BaseModel):
    name: str


class ClientApplicationCreate(ClientApplicationBase):
    pass


class ClientApplicationOut(ClientApplicationBase):
    client_id: str
    is_active: bool
    groups: GroupOut
    permissions: list["PermissionUpdate"] = Field(default_factory=list)


class TokenData(BaseModel):
    sub: str
    client_type: ClientType


class Token(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
