import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from Services.Users.schema import UserCreate, UserRead
from Services.Users.serivce import users_service
from Shared.Auth.auth import get_me
from Shared.CustomError.custom_error import NotFoundInDBError, NotValidPassword


auth_router = APIRouter()


@auth_router.post('/register', name='register user', status_code=201, response_model=UserRead)
async def create_user(user: UserCreate, users=users_service):
    user =  await users.create_user({**user.__dict__})
    logging.info(f"Create user: {user.name}")

    return user


@auth_router.post('/refresh')
async def refresh(refresh_token: str = None, me=Depends(get_me), users=users_service):
    try:
        access_info = await users.refresh(refresh_token)
        response = JSONResponse(content=access_info)
        response.set_cookie(key="access_token", value=access_info.get('access_token'), secure=True, samesite="none")
        response.headers["Authorization"] = f"Bearer {access_info.get('access_token')}"
        logging.info("Refresh access token")

        return response
    except NotFoundInDBError:
        raise HTTPException(status_code=404, detail='Пользователь не найден')



@auth_router.post('/login', name='login')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), users=users_service):
    try:
        access_info = await users.login(form_data)
        response = JSONResponse(content=access_info)
        response.set_cookie(key="refresh_token", value=access_info.get('refresh_token'), secure=True, samesite="none")
        response.set_cookie(key="access_token", value=access_info.get('access_token'), secure=True, samesite="none")
        response.headers["Authorization"] = f"Bearer {access_info.get('access_token')}"

        logging.info(f"User {form_data.username} - logged in")

        return response
    except NotFoundInDBError:
        raise HTTPException(status_code=404, detail='Пользователь не найден')
    except NotValidPassword:
        raise HTTPException(status_code=400, detail='Неверный пароль')
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

