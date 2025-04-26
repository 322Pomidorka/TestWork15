from fastapi import Depends
from sqlalchemy import or_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from Services.Tasks.model import Task
from Shared.Base.BaseRepository import BaseRepository
from Shared.Database.Sessions import get_session
from Shared.Utils.Handle_db_errors import handle_db_errors


class TasksRepository(BaseRepository):
    model = Task


    @handle_db_errors
    async def search_tasks(self, search_term: str):
        """search term in  tasks title/description"""

        search_filter = or_(
            func.lower(Task.title).contains(func.lower(search_term)),
            func.lower(Task.description).contains(func.lower(search_term))
        )

        query = select(self.model).filter(search_filter)
        result = await self.session.execute(query)

        return result.scalars().all()



async def get_tasks_repository(session: AsyncSession = Depends(get_session)):
    return TasksRepository(session)


tasks_repository: TasksRepository = Depends(get_tasks_repository)