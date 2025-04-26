import contextlib
from typing import AsyncIterator

import pytest
import sqlalchemy.engine.url as SQURL
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncConnection

from Services.Tasks.model import Task
from Services.Users.model import User
from Shared.Base.BaseModel import Base
from Shared.Base.Settings import Settings

TEST_DATABASE_URL = SQURL.URL.create(
    drivername="postgresql+asyncpg",
    username=Settings.database.user,
    password=Settings.database.password,
    host=Settings.database.host,
    port=Settings.database.port,
    database=Settings.database.database + '_test',
)

class TestingAsyncDBSessions:
    def __init__(self):
        self.__URL = TEST_DATABASE_URL
        self._engine = create_async_engine(self.__URL, pool_size=5, max_overflow=10)
        self._sessionmaker = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)

    def get_url(self):
        return str(self.__URL)

    async def get_session(self) -> None:
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    async def close(self) -> None:
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise IOError("DatabaseSessionManager is not initialized")
        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise IOError

TestingAsyncDatabase = TestingAsyncDBSessions()

@pytest.fixture(scope="session", autouse=True)
async def create_test_database():
    """
    Creates a test database and applies migrations (if needed).
    This fixture runs once per test session.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


    yield # Provide the connection

    # Clean up after all tests are finished
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
    await engine.dispose()

@pytest.fixture(scope="function")
async def get_test_session() -> AsyncSession:
    """
    Yields a new session for each test function.
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        await session.begin()
        yield session
        await session.rollback()

@pytest.mark.asyncio
async def test_create_and_read_task(get_test_session):
    """
    Tests creating a task and then reading it from the database.
    """
    async with get_test_session as session:

        # Create a new User object
        new_user = User(
            name="User",
            email="test@example.com",
            password=User.hash_password("password123"),
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Create a new Task object and associate it with the user
        new_task = Task(
            customer_name="Test Customer",
            title="Test Task",
            description="This is a test task description.",
            user_id=new_user.id,
        )

        session.add(new_task)
        await session.commit()

        await session.refresh(new_task)

        assert new_task.id is not None

        retrieved_task = await session.get(Task, new_task.id)

        assert retrieved_task is not None
        assert retrieved_task.title == "Test Task"
        assert retrieved_task.description == "This is a test task description."
        assert retrieved_task.customer_name == "Test Customer"
        assert retrieved_task.user_id == new_user.id
        assert retrieved_task.user.name == "User"


@pytest.mark.asyncio
async def test_delete_task(get_test_session):
    """
    Tests deleting a task from the database.
    """
    async with get_test_session as session:
        # Create a new User object
        new_user2 = User(
            name="User2",
            email="test2@example.com",
            password=User.hash_password("password1232"),
        )
        session.add(new_user2)
        await session.commit()
        await session.refresh(new_user2)

        # Create a new Task object and associate it with the user
        new_task = Task(
            customer_name="Test Customer",
            title="Test Task",
            description="Test Task description.",
            user_id=new_user2.id,
        )

        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

        await session.delete(new_task)
        await session.commit()

        deleted_task = await session.get(Task, new_task.id)

        assert deleted_task is None


@pytest.mark.asyncio
async def test_update_task(get_test_session):
    """
    Tests updating an existing task in the database.
    """
    async with get_test_session as session:
        # Create a new User object
        new_user1 = User(
            name="User1",
            email="test1@example.com",
            password=User.hash_password("password1234"),
        )
        session.add(new_user1)
        await session.commit()
        await session.refresh(new_user1)

        # Create a new Task object and associate it with the user
        new_task = Task(
            customer_name="Test Customer",
            title="Test Task",
            description="Test Task description.",
            user_id=new_user1.id,
        )

        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

        new_task.title = "Updated Task Title"
        new_task.status = "done"
        await session.commit()

        updated_task = await session.get(Task, new_task.id)

        assert updated_task is not None
        assert updated_task.title == "Updated Task Title"
        assert updated_task.status == "done"


