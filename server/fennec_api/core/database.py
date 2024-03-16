from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fennec_api.core.config import settings
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DB_URI)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
