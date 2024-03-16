from pydantic import EmailStr
from fennec_api.core.schemas import FennecBaseModel


class Token(FennecBaseModel):
    access_token: str
    token_type: str


class TokenData(FennecBaseModel):
    email: EmailStr
