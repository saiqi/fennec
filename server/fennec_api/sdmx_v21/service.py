from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_api.core.crud import CRUDBase
from fennec_api.sdmx_v21.models import Provider
from fennec_api.sdmx_v21.schemas import ProviderCreate, ProviderUpdate

crud_provider = CRUDBase[Provider, ProviderCreate, ProviderUpdate](Provider)


async def get_provider(session: AsyncSession, *, id: int) -> Provider | None:
    return await crud_provider.get(session, id=id)


async def list_providers(
    session: AsyncSession, *, offset: int, limit: int
) -> Sequence[Provider]:
    return await crud_provider.get_multi(session, offset=offset, limit=limit)


async def create_provider(session: AsyncSession, *, obj_in: ProviderCreate) -> Provider:
    return await crud_provider.create(session, obj_in=obj_in)


async def update_provider(
    session: AsyncSession, *, db_obj: Provider | None, obj_in: ProviderUpdate
) -> Provider | None:
    return await crud_provider.update(session, obj_in=obj_in, db_obj=db_obj)


async def delete_provider(
    session: AsyncSession, *, db_obj: Provider | None
) -> Provider | None:
    return await crud_provider.delete(session, db_obj=db_obj)
