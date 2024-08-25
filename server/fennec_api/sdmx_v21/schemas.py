from pydantic import HttpUrl
from fennec_api.core.schemas import FennecBaseModel


class ProviderBase(FennecBaseModel):
    agency_id: str
    root_url: HttpUrl
    bulk_download: bool
    skip_categories: bool
    process_all_agencies: bool


class ProviderCreate(ProviderBase):
    pass


class ProviderUpdate(ProviderBase):
    pass


class ProviderRead(ProviderBase):
    id: int
