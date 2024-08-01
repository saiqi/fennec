from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_api.core.database import SessionLocal
from fennec_api.core.arq import redis_settings


async def startup(ctx: dict[str, Any]) -> None:
    ctx["session"] = SessionLocal()


async def shutdown(ctx: dict[str, Any]) -> None:
    session: AsyncSession = ctx["session"]
    await session.aclose()


async def health_check_task(ctx: dict[str, Any]) -> None:
    session: AsyncSession = ctx["session"]
    await session.execute(text("SELECT 1"))


class WorkerSettings:
    functions = [health_check_task]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings
