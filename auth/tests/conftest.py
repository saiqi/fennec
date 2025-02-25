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
from fennec_auth.models import Group, User, ClientApplication
from fennec_auth.security import get_password_hash
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


@pytest_asyncio.fixture()
async def existing_user(session: AsyncSession) -> AsyncGenerator[User, None]:
    user = User(
        first_name="Fleury",
        last_name="Dinallo",
        user_name="fleury",
        email="fleury@redstarfc.fr",
        role="read",
        password_hash=get_password_hash("password"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    yield user


@pytest_asyncio.fixture()
async def existing_group(session: AsyncSession) -> AsyncGenerator[Group, None]:
    group = Group(name="red-star")
    session.add(group)
    await session.commit()
    await session.refresh(group)
    yield group


@pytest_asyncio.fixture()
async def existing_client_application(
    session: AsyncSession,
) -> AsyncGenerator[ClientApplication, None]:
    client_application = ClientApplication(
        name="red-star-api",
        client_id="red-star-api",
        client_secret_hash=get_password_hash("secret"),
        is_active=True,
    )
    session.add(client_application)
    await session.commit()
    await session.refresh(client_application)
    yield client_application


@pytest_asyncio.fixture()
async def existing_alt_client_application(
    session: AsyncSession,
) -> AsyncGenerator[ClientApplication, None]:
    client_application = ClientApplication(
        name="red-star-auth",
        client_id="red-star-auth",
        client_secret_hash=get_password_hash("secret"),
        is_active=True,
    )
    session.add(client_application)
    await session.commit()
    await session.refresh(client_application)
    yield client_application
