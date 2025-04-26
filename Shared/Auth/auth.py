import logging
import string
from datetime import datetime, timedelta
import random

import bcrypt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from jose import jwt

from Services.Users.model import User
from Shared.Database.Sessions import get_session
from Shared.Base.Settings import Settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login", scheme_name="JWT")


async def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
        Creating a token with a lifetime
    """
    try:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=int(Settings.auth.access_token_expire_minutes))
        to_encode = data | {"exp": expire}
        encoded_jwt = jwt.encode(to_encode, Settings.auth.secret_key, algorithm=Settings.auth.algorithm)

        logging.info(f"create token")

        return encoded_jwt
    except Exception as e:
        logging.error(f"Failed create token: {e}")
        raise


async def create_refresh_token(data: dict) -> str:
    return await create_access_token(data, expires_delta=timedelta(days=7)) # 7 days for refresh


async def password_generator():
    """
         generate a password using letters, numbers, and special char.
    """
    length = random.randint(8, 12)
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(random.choice(characters) for i in range(length))
    return password


async def hash_password(password):
    """
        hashing the password
    """
    if not password:
        password = await password_generator()
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def get_me(token: str = Depends(oauth2_scheme), session = Depends(get_session)):
    """Get user info by token"""

    if not token:
        logging.error(f"Token not provided")
        raise HTTPException(status_code=401, detail="Token not provided")
    try:
        payload = jwt.decode(token=token, key=Settings.auth.secret_key, algorithms=[Settings.auth.algorithm])

    except jwt.ExpiredSignatureError:
        logging.error(f"Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception as e:
        logging.error("Invalid token: " + str(e))
        raise HTTPException(status_code=401, detail="Invalid token: " + str(e))

    if payload.get("exp") and payload["exp"] < datetime.timestamp(datetime.utcnow()):
        logging.error(f"Token has expired")
        raise HTTPException(status_code=401, detail="Token expired")

    try:
        user = await session.get(User, int(payload.get('user_id')))
        if user.active is False:
            logging.error(f"User deactivate")
            raise HTTPException(status_code=401, detail="User deactivate")
        return user
    except Exception as e:
        logging.error(f"unexpected error: {e}")
        raise HTTPException(status_code=500, detail="unexpected")
    finally:
        await session.close()