from typing import Protocol, Callable
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin
from httpx import AsyncClient


class StructureType(str, Enum):
    DATASTRUCTURE = "datastructure"
    CATEGORYSCHEME = "categoryscheme"
    CONCEPTSCHEME = "conceptscheme"
    CODELIST = "codelist"
    AGENCYSCHEME = "agencyscheme"
    DATAFLOW = "dataflow"
    CATEGORISATION = "categorisation"
    CONTENTCONSTRAINT = "contentconstraint"


class DetailType(str, Enum):
    ALLSTUBS = "allstubs"
    REFERENCESTUBS = "referencestubs"
    ALLCOMPLETESTUBS = "allcompletestubs"
    REFERENCECOMPLETESTUBS = "referencecompletestubs"
    REFERENCEPARTIAL = "referencepartial"
    FULL = "full"


class ReferencesType(str, Enum):
    NONE = "none"
    PARENTS = "parents"
    PARENTSANDSIBLINGS = "parentsandsiblings"
    CHILDREN = "children"
    DESCENDANTS = "descendants"
    ALL = "all"


STRUCTURE_CONTENT_TYPE = "application/vnd.sdmx.structure+xml;version=2.1"


@dataclass
class SDMX21StructureRequest:
    resource: StructureType
    agency_id: str | None = None
    resource_id: str | None = None
    version: str | None = None
    item_id: str | None = None


class ISDMX21RestClient(Protocol):
    async def get_structure(
        self,
        *,
        req: SDMX21StructureRequest,
        detail: DetailType | None = None,
        references: ReferencesType | None = None,
    ) -> bytes: ...


def build_default_structure_path(req: SDMX21StructureRequest) -> str:
    path_elems = [req.resource.value]
    if req.agency_id:
        path_elems.append(req.agency_id)
    if req.resource_id:
        path_elems.append(req.resource_id)
    if req.version:
        path_elems.append(req.version)
    if req.item_id:
        path_elems.append(req.item_id)
    return "/".join(path_elems)


def build_default_structure_params(
    detail: DetailType | None, references: ReferencesType | None
) -> dict[str, str]:
    params = {}
    if detail:
        params["detail"] = detail.value
    if references:
        params["references"] = references.value
    return params


def build_default_structure_headers() -> dict[str, str]:
    return {"Accept": STRUCTURE_CONTENT_TYPE}


class SDMX21RestClient(ISDMX21RestClient):
    def __init__(
        self,
        http_client: AsyncClient,
        root_url: str,
        path_builder: Callable[
            [SDMX21StructureRequest], str
        ] = build_default_structure_path,
        params_builder: Callable[
            [DetailType | None, ReferencesType | None], dict[str, str]
        ] = build_default_structure_params,
        headers_builder: Callable[[], dict[str, str]] = build_default_structure_headers,
    ) -> None:
        self.http_client = http_client
        self.root_url = root_url
        self.path_builder = path_builder
        self.params_builder = params_builder
        self.headers_builder = headers_builder

    async def __do_request(
        self,
        *,
        path: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> bytes:
        url = urljoin(self.root_url, path)
        r = await self.http_client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.content

    async def get_structure(
        self,
        *,
        req: SDMX21StructureRequest,
        detail: DetailType | None = None,
        references: ReferencesType | None = None,
    ) -> bytes:
        return await self.__do_request(
            path=self.path_builder(req),
            params=self.params_builder(detail, references),
            headers=self.headers_builder(),
        )
