from enum import StrEnum, auto
from pydantic import EmailStr, ConfigDict
from fennec_api.core.schemas import FennecBaseModel


class Role(StrEnum):
    ADMIN = auto()
    WRITE = auto()
    READ = auto()


class UserBase(FennecBaseModel):
    email: EmailStr | None = None
    disabled: bool = False
    role: Role | None = None


class UserCreate(FennecBaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserUpdatePassword(FennecBaseModel):
    password: str


class UserUpdateStatus(FennecBaseModel):
    disabled: bool


class UserUpdateRole(FennecBaseModel):
    role: Role


class UserInDb(UserBase):
    hashed_password: str
