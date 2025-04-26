from datetime import datetime
from typing import Any

from sqlalchemy import Column
from fastapi import Depends

from Services.Tasks.repository import TasksRepository, get_tasks_repository


class TasksService:

    def __init__(self, repository: TasksRepository = Depends(get_tasks_repository)):
        self._repository = repository


    async def get_by_filters(self, created_after: datetime, filters: dict[Column[Any], Any | None] | None = None):
        """get tasks by filters (created_at, status, priority)"""
        return await self._repository.get_by_filters(created_after, filters)


    async def search_tasks(self, search_term: str):
        """Search tasks"""
        return await self._repository.search_tasks(search_term)


    async def create_task(self, task: dict):
        """Create task"""
        return await self._repository.create(task)


    async def update_task(self, data: dict, task_id: str):
        """Update task"""
        task = await self._repository.id(int(task_id))

        return await self._repository.update(task, data)


async def get_tasks_service(repository: TasksRepository = Depends(get_tasks_repository)):
    return TasksService(repository=repository)


tasks_service: TasksService = Depends(get_tasks_service)