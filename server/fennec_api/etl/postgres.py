from typing import TypeVar, Any, Type, Iterable
from itertools import batched
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from fennec_api.core.database import Base


ModelType = TypeVar("ModelType", bound=Base)


async def upsert(
    session: AsyncSession,
    *,
    model: Type[ModelType],
    records: Iterable[dict[str, Any]],
    chunk_size: int = 1000,
) -> None:
    mapper = inspect(model)

    for batch in batched(records, n=chunk_size):
        insert_statement = insert(model).values(list(batch))
        do_update_statement = insert_statement.on_conflict_do_update(
            index_elements=[c.description for c in mapper.primary_key],
            set_={
                c.description: insert_statement.excluded[c.description]
                for c in mapper.columns
                if not c.primary_key
            },
        )
        await session.execute(do_update_statement)
        await session.commit()
