import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from starlette import status

from tests.test_db import TEST_DATABASE_URL
from Services.Tasks.model import Task
from Services.Tasks.schema import TaskStatus, TaskPriority
from Services.Users.model import User
from Shared.Base.BaseModel import Base
from Shared.Database.Sessions import get_session
from app import app


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)


# Создаем асинхронную сессию
TestingAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Функция для подмены зависимости get_session
async def override_get_session():
    async with TestingAsyncSessionLocal() as session:
        yield session


# Функция для подмены зависимостей в тестах
def override_dependencies():
    app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="function")
async def create_test_database():
    """Создает таблицы перед каждым тестом и удаляет данные после."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def cleanup_tables(create_test_database):
    """Очистка таблиц после каждого теста."""
    async with AsyncSession(test_engine) as session:
        await session.execute(delete(Task))
        await session.execute(delete(User))
        await session.commit()


# Выполняем подмену зависимостей
override_dependencies()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def ac(event_loop) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

async def register_user(ac: AsyncClient, user_data) -> dict:
    """Регистрирует пользователя и возвращает данные пользователя."""
    response = await ac.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


async def login_user(ac: AsyncClient, username: str, password: str) -> dict:
    """Логинит пользователя и возвращает токены."""
    form_data = {"username": username, "password": password}
    response = await ac.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def create_authorized_client(ac: AsyncClient, username: str, password: str):
    """Регистрирует, логинит пользователя и возвращает клиент с токеном авторизации."""
    user_data = {
        "name": username,
        "email": f"{username}.mail.ru",
        "password": password,
    }
    await register_user(ac, user_data)
    login_data = await login_user(ac, username, password)
    access_token = login_data["access_token"]
    ac.headers["Authorization"] = f"Bearer {access_token}"  # Добавляем токен в заголовок

    return ac, login_data


async def create_task(authorized_client, task_data):
    # Создаём таск
    response = await authorized_client.post("/api/v1/tasks/tasks", json=task_data)
    assert response.status_code == status.HTTP_201_CREATED

    return response.json()


@pytest.mark.asyncio
async def test_get_by_filters(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for getting tasks by filters."""

    authorized_client, login_data = await create_authorized_client(ac, "sdsdfsadfasd", "password123")

    task_data = {
        'title': 'test',
        'description': 'test',
        'status': TaskStatus.PENDING,
        'priority': TaskPriority.MEDIUM
    }

    await create_task(authorized_client, task_data)

    task_data = {
        'title': 'test2',
        'description': 'test2',
        'status': TaskStatus.DONE,
        'priority': TaskPriority.LOWEST
    }

    await create_task(authorized_client, task_data)

    response = await authorized_client.get(f"/api/v1/tasks/tasks?status=done")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "test2"

    created_after = datetime.now() - timedelta(days=1)
    response = await authorized_client.get(f"/api/v1/tasks/tasks?created_after={created_after.isoformat()}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_create_tasks(ac: AsyncClient, create_test_database, cleanup_tables):
    authorized_client, login_data = await create_authorized_client(ac,
                                                                   "authuser2@example.com",
                                                                   "password123")

    task_data = {
        'title': 'test',
        'description': 'test',
        'status': TaskStatus.PENDING,
        'priority': TaskPriority.MEDIUM
    }

    await create_task(authorized_client, task_data)


@pytest.mark.asyncio
async def test_update_task(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for updating a task."""
    authorized_client, login_data = await create_authorized_client(ac, "test232fd", "password123")

    task_data = {
        'title': 'test',
        'description': 'test',
        'status': TaskStatus.PENDING,
        'priority': TaskPriority.MEDIUM
    }

    task = await create_task(authorized_client, task_data)

    update_data = {
        "id": task['id'],
        "title": "Updated Task",
        "description": "Updated Description"
    }

    response = await authorized_client.put(f"/api/v1/tasks/tasks/{update_data['id']}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == task['id']
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated Description"


@pytest.mark.asyncio
async def test_search_tasks(ac: AsyncClient,  create_test_database, cleanup_tables):
    authorized_client, login_data = await create_authorized_client(ac, "test232fd", "password123")

    task_data = {
        'title': 'test',
        'description': 'test',
        'status': TaskStatus.PENDING,
        'priority': TaskPriority.MEDIUM
    }

    await create_task(authorized_client, task_data)
    search_term = "tes"

    response = await authorized_client.get(f"/api/v1/tasks/tasks/search?search_term={search_term}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "test"