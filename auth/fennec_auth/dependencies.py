from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fennec_auth.database import SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
