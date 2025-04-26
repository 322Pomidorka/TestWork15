import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query

from Services.Tasks.model import Task
from Shared.Auth.auth import get_me
from Services.Tasks.schema import CreateTask, TaskUpdate, TaskStatus, TaskPriority
from Services.Tasks.serivce import tasks_service

tasks_router = APIRouter()


@tasks_router.get('/tasks', name='получение списка задач с фильтрацией по статусу, приоритету, дате создания')
async def tasks_by_filter(
        created_at: datetime | None = Query(None,
                                            description="Дата создания в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        tasks = tasks_service,
        me=Depends(get_me)
):
    try:
        filters = {
            Task.status: status,
            Task.priority: priority
        }

        db_tasks = await tasks.get_by_filters(created_at, filters)
        logging.info(f"Get tasks by filters")

        return db_tasks
    except Exception as e:
        logging.error(f"Unexpected error in get tasks by filters: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=e)


@tasks_router.get('/tasks/search', name='поиск задач по подстроке в названии или описании')
async def search_tasks(
    search_term: str,
    tasks = tasks_service,
    me=Depends(get_me)
):
    try:
        db_tasks = await tasks.search_tasks(search_term)
        return db_tasks
    except Exception as e:
        logging.error(f"Unexpected error in search tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=e)


@tasks_router.post('/tasks', name='создание задачи', status_code=201)
async def create_tasks(task: CreateTask, tasks = tasks_service, me=Depends(get_me)):
    try:
        db_task = await tasks.create_task({**task.__dict__, "customer_name": me.name, "user_id": me.id})
        logging.info(f"Tasks created: {db_task.id}")

        return db_task
    except Exception as e:
        logging.error(f"Unexpected error in create tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=e)


@tasks_router.put('/tasks/{task_id}', name='обновление задачи')
async def update_task(task_id: str, update_data: TaskUpdate, tasks = tasks_service, me=Depends(get_me)):
    try:
        db_task = await tasks.update_task({**update_data.__dict__}, task_id)
        logging.info(f"Task {task_id} updated", exc_info=True)

        return db_task
    except Exception as e:
        logging.error(f"Unexpected error in create tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=e)
