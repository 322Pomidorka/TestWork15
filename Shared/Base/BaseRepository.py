import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, Column
from sqlalchemy.ext.asyncio import AsyncSession

from Shared.CustomError.custom_error import NotFoundInDBError
from Shared.Utils.Handle_db_errors import handle_db_errors


class BaseRepository:
    """
        Base DB manager
    """

    model = None

    def __init__(self, session):
        self.session: AsyncSession = session


    @handle_db_errors
    async def id(self, model_id: int):
        model = await self.session.get(self.model, model_id)
        if model is not None:
            return model
        raise NotFoundInDBError


    @handle_db_errors
    async def all(self):
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()


    @handle_db_errors
    async def create(self, data: dict):
        model = self.model(**data)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model


    @handle_db_errors
    async def delete(self, model_id: int):
        model = await self.id(model_id)
        if not model:
            raise NotFoundInDBError
        await self.session.delete(model)
        await self.session.commit()
        return 200


    @handle_db_errors
    async def update(self, instance , update_data: dict):
        """
            Update model instance
            excluding None values,and sets updated_at to the current time.
        """
        for key, value in update_data.items():
            if value is None:
                continue

            if hasattr(instance , key):
                try:
                    if isinstance(value, datetime) and value.tzinfo is not None:
                        value = value.replace(tzinfo=None)

                    setattr(instance , key, value)
                except AttributeError:
                    logging.error(f"The {key} field cannot be changed directly")
                    continue
            else:
                logging.error(f"The {key} field was not found in the model {instance .__class__.__name__}")
                raise ValueError

        instance .updated_at = datetime.utcnow()
        await self.session.commit()
        return instance


    @handle_db_errors
    async def get_by_filters(self, created_after: datetime = None, filters: dict[Column[Any], Any | None] | None = None):
        query = select(self.model)

        if filters:
            for column, value in filters.items():
                if value is not None:
                    query = query.filter(column == value)

        if created_after:
            query = query.filter(self.model.created_at >= created_after)

        result = await self.session.execute(query)
        return result.scalars().all()

