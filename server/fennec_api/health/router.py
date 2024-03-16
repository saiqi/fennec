from typing import Annotated, Any
import asyncio
import socket
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fennec_api.core.dependencies import get_session
from fennec_api.health.schemas import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=200, response_model=HealthCheckResponse)
async def health_check(session: Annotated[AsyncSession, Depends(get_session)]) -> Any:
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=1)
    except (asyncio.TimeoutError, socket.gaierror):
        return Response(status_code=503)
    return {"message": "Healthy"}
