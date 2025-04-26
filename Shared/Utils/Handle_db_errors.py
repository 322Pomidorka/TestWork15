import logging
from functools import wraps

from sqlalchemy.exc import SQLAlchemyError
from typing_extensions import Any


def handle_db_errors(func):
    """
    Декоратор для обработки ошибок SQLAlchemy
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            logging.error(f"Database error in the function '{func.__name__}': {e}")
            session = args[0].session
            await session.rollback()
            raise
        except Exception as e:
            logging.error(f"Unexpected error '{func.__name__}': {e}")
            raise

    return wrapper