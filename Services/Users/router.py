import logging

from fastapi import APIRouter, HTTPException

from Services.Users.serivce import users_service

users_router = APIRouter()


@users_router.get('/users/', name='получение всех пользователей')
async def all_users(user = users_service):
    try:
        db_users =  await user.get_all_users()
        logging.info(f"Get all users")

        return db_users
    except Exception as e:
        logging.error(f"Failed get all users: {e}")
        raise HTTPException(status_code=500, detail=e)