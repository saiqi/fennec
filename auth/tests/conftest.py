from dotenv import load_dotenv

load_dotenv(".unittest.env", override=True)

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from httpx import AsyncClient, ASGITransport
from fennec_auth.database import Base, engine
from fennec_auth.dependencies import get_session
from fennec_auth.main import app


@pytest_asyncio.fixture()
async def connection() -> AsyncGenerator[AsyncConnection, None]:
    async with engine.connect() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        yield connection
        await connection.rollback()


@pytest_asyncio.fixture()
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(connection, expire_on_commit=False) as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def override_dependencies(session: AsyncSession) -> None:
    app.dependency_overrides[get_session] = lambda: session


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        base_url="http://test",
        transport=ASGITransport(app=app),
    ) as client:
        yield client
