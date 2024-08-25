from typing import TypeVar, Type, Generic, Any, Sequence
from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from fennec_api.core.schemas import FennecBaseModel
from fennec_api.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=FennecBaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=FennecBaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model

    async def create(
        self, session: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        return db_obj

    async def get(
        self, session: AsyncSession, *args: Any, **kwargs: Any
    ) -> ModelType | None:
        result = await session.execute(
            select(self._model).filter(*args).filter_by(**kwargs)
        )
        return result.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        *args: Any,
        offset: int = 0,
        limit: int = -1,
        **kwargs: Any,
    ) -> Sequence[ModelType]:
        stmt = (
            (
                select(self._model)
                .filter(*args)
                .filter_by(**kwargs)
                .offset(offset)
                .limit(limit)
            )
            if limit >= 0
            else (select(self._model).filter(*args).filter_by(**kwargs).offset(offset))
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    async def update(
        self,
        session: AsyncSession,
        *,
        obj_in: UpdateSchemaType | dict[str, Any],
        db_obj: ModelType | None,
        **kwargs: Any,
    ) -> ModelType | None:
        db_obj = db_obj or await self.get(session, **kwargs)
        if not db_obj:
            return None
        obj_data = {
            c.key: getattr(db_obj, c.key)
            for c in inspect(self._model).mapper.column_attrs
        }
        update_data = jsonable_encoder(
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        return db_obj

    async def delete(
        self, session: AsyncSession, *args: Any, db_obj: ModelType | None, **kwargs: Any
    ) -> ModelType | None:
        db_obj = db_obj or await self.get(session, *args, **kwargs)
        await session.delete(db_obj)
        await session.commit()
        return db_obj
