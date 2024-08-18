from typing import Annotated, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Body, Query, status, HTTPException
from fennec_api.auth.dependencies import get_current_admin
from fennec_api.users.models import User
from fennec_api.core.dependencies import get_session
from fennec_api.sdmx_v21.schemas import ProviderCreate, ProviderRead, ProviderUpdate
import fennec_api.sdmx_v21.service as service


router = APIRouter(prefix="/sdmx", tags=["SDMX"])


@router.post(
    "/providers", status_code=status.HTTP_201_CREATED, response_model=ProviderRead
)
async def create_providers(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_admin)],
    provider_data: Annotated[ProviderCreate, Body(...)],
) -> Any:
    return await service.create_provider(session, obj_in=provider_data)


@router.get(
    "/providers", status_code=status.HTTP_200_OK, response_model=list[ProviderRead]
)
async def list_providers(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_admin)],
    offset: Annotated[int, Query(...)] = 0,
    limit: Annotated[int, Query(...)] = 100,
) -> Any:
    return await service.list_providers(session, offset=offset, limit=limit)


@router.get(
    "/providers/{id}", status_code=status.HTTP_200_OK, response_model=ProviderRead
)
async def get_provider(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_admin)],
    id: int,
) -> Any:
    provider = await service.get_provider(session, id=id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find provider {id}",
        )
    return provider


@router.put(
    "/providers/{id}", status_code=status.HTTP_200_OK, response_model=ProviderRead
)
async def update_provider(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_admin)],
    id: int,
    provider_data: Annotated[ProviderUpdate, Body(...)],
) -> Any:
    provider = await service.get_provider(session, id=id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find provider {id}",
        )
    return await service.update_provider(session, db_obj=provider, obj_in=provider_data)
