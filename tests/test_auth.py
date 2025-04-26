import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from starlette import status


from tests.test_db import TEST_DATABASE_URL
from Services.Users.model import User
from Shared.Base.BaseModel import Base
from Shared.Database.Sessions import get_session
from app import app


# Создаем асинхронный движок
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
        "name": "testuser",
        "email": username,
        "password": password,
    }
    await register_user(ac, user_data)
    login_data = await login_user(ac, username, password)
    access_token = login_data["access_token"]
    ac.headers["Authorization"] = f"Bearer {access_token}"  # Добавляем токен в заголовок

    return ac, login_data


@pytest.mark.asyncio
async def test_register_user(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for user registration"""
    test_user = {
        "name": "tes1tusersdfsd",
        "email": "sd1fasdf@example.com",
        "password": "password123"
    }
    response = await register_user(ac, test_user)
    assert response["name"] == test_user["name"]
    assert response["email"] == test_user["email"]


@pytest.mark.asyncio
async def test_login_user(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for user login"""
    authorized_client, login_data = await create_authorized_client(ac, "authuser2@example.com", "password123")
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_invalid_credentials(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for login with invalid credentials"""
    form_data = {"username": "nonexistentuser789", "password": "wrongpassword"}
    response = await ac.post("/api/v1/auth/login", data=form_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_refresh_token(ac: AsyncClient, create_test_database, cleanup_tables):
    """Test for token refreshing"""
    authorized_client, login_data = await create_authorized_client(ac, "authuser2@example.com", "password123")

    response = await authorized_client.post(f"/api/v1/auth/refresh?refresh_token={str(login_data['refresh_token'])}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    app.dependency_overrides = {}