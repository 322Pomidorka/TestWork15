import logging

import uvicorn
from fastapi import APIRouter, FastAPI

from Services.Tasks.router import tasks_router
from Services.Users.auth_router import auth_router
from Services.Users.router import users_router

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


app = FastAPI(docs_url='/api/docs')

# Routers
router = APIRouter()
# Users
router.include_router(users_router, tags=['Users | users'], prefix='/users')
# Tasks
router.include_router(tasks_router, tags=['Tasks | tasks'], prefix='/tasks')
# Auth
router.include_router(auth_router, tags=['Auth | auth'], prefix='/auth')


app.include_router(router, prefix='/api/v1')


if __name__ == '__main__':
    uvicorn.run("app:app", host='0.0.0.0', port=8008, reload=True)