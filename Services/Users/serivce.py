import logging

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from Shared.Auth.auth import create_access_token, create_refresh_token, hash_password
from Shared.CustomError.custom_error import NotFoundInDBError, NotValidPassword
from Services.Users.repository import get_users_repository, UsersRepository



class UsersService:

    def __init__(self, repository: UsersRepository = Depends(get_users_repository)):
        self._repository = repository


    async def get_all_users(self):
        """
            Получение всех пользователей
        """
        return await self._repository.all()



    async def create_user(self, user_data: dict):
        """
            Создание пользователя
        """

        user_data["password"] = await hash_password(user_data["password"])
        return await self._repository.create(user_data)


    async def refresh(self, refresh_token: str):
        """
            Обновление access token
        """

        try:
            user = await self._repository.get_user_by_refresh_token(refresh_token)

            to_encode = {"user_id": str(user.id), "name": user.name}
            access_token = await create_access_token(data=to_encode)

            return {"access_token": access_token, "token_type": "bearer"}
        except:
            raise


    async def login(self, login: OAuth2PasswordRequestForm = Depends()):
        """
            Авторизация пользователя
            создаём новому пользователю access\refresh token
        """
        user = await self._repository.get_user_by_login(login.username)

        if not user:
            logging.error("User not found")
            raise NotFoundInDBError
        if not user.verify_password(login.password, user.password):
            logging.error("Not valid password")
            raise NotValidPassword

        to_encode = {"user_id": str(user.id),
                     "name": user.name}

        access_token = await create_access_token(data=to_encode)
        refresh_token = await create_refresh_token(data=to_encode)

        await self._repository.update(user, {"refresh_token": refresh_token})

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def get_users_service(repository: UsersRepository = Depends(get_users_repository)):
    return UsersService(repository=repository)


users_service: UsersService = Depends(get_users_service)