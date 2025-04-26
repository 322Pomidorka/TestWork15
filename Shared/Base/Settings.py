from dataclasses import dataclass
from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: str
    url: str


@dataclass
class Auth:
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


@dataclass
class Config:
    database: DbConfig
    auth: Auth


def get_settings():
    path = '.env'
    env = Env()
    env.read_env(path)

    return Config(
        database=DbConfig(
            host=env.str('DB_LB_HOST'),
            password=env.str('DB_PASSWORD'),
            user=env.str('DB_USER'),
            database=env.str('POSTGRES_DB'),
            port=env.str('DB_LB_PORT'),
            url=f"postgresql+asyncpg://{env.str('DB_USER')}:{env.str('DB_PASSWORD')}@{env.str('DB_LB_HOST')}:{env.str('DB_LB_PORT')}/{env.str('POSTGRES_DB')}",
        ),
        auth=Auth(
            secret_key=env.str('SECRET_KEY'),
            algorithm=env.str('ALGORITHM'),
            access_token_expire_minutes=env.str('ACCESS_TOKEN_EXPIRE_MINUTES'),
        ),
    )


Settings = get_settings()
