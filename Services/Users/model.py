import bcrypt

from sqlalchemy.orm import Mapped, mapped_column, relationship

from Services.Tasks.model import Task
from Shared.Base.BaseModel import Base


class User(Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    email:Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(nullable=True)

    tasks: Mapped[list["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")


    @staticmethod
    def verify_password(password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')