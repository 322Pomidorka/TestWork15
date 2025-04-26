import contextlib
from typing import AsyncIterator

import sqlalchemy.engine.url as SQURL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncConnection

from Shared.Base.Settings import Settings


class AsyncDBSessions:

    def __init__(self):
        self._URL = SQURL.URL.create(
            drivername="postgresql+asyncpg",
            username=Settings.database.user,
            password=Settings.database.password,
            host=Settings.database.host,
            port=Settings.database.port,
            database=Settings.database.database,
        )
        self._engine = create_async_engine(self._URL,
                                          pool_size=5,
                                          max_overflow=10,)
        self._sessionmaker = async_sessionmaker(self._engine, class_=AsyncSession, expire_on_commit=False)


    def get_url(self):
        return str(self._URL)


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
            raise IOError("DatabaseSessionManager is not initialized")
        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise


AsyncDatabase = AsyncDBSessions()


async def get_session() -> AsyncSession:
    async with AsyncDatabase.session() as session:
        yield session
