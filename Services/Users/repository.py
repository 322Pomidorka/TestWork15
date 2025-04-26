from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from Services.Users.model import User
from Shared.Base.BaseRepository import BaseRepository
from Shared.Database.Sessions import get_session
from Shared.CustomError.custom_error import NotFoundInDBError


class UsersRepository(BaseRepository):
    model = User

    async def get_user_by_login(self, login: str) -> User:
        query = select(User).where(func.lower(User.name) == login.strip().lower())
        result = await self.session.scalars(query)
        user = result.first()

        if not user:
            query = select(User).where(func.lower(User.email) == login.strip().lower())
            result = await self.session.scalars(query)
            user = result.first()

        return user


    async def get_user_by_refresh_token(self, refresh_token: str) -> User:
        query = await self.session.scalars(select(User).where(User.refresh_token == refresh_token))
        user = query.first()
        if not user:
            raise NotFoundInDBError

        return user


async def get_users_repository(session: AsyncSession = Depends(get_session)):
    return UsersRepository(session)


users_repository: UsersRepository = Depends(get_users_repository)