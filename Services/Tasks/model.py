from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from Services.Tasks.schema import TaskStatus, TaskPriority
from Shared.Base.BaseModel import Base


class Task(Base):
    __tablename__ = "tasks"


    customer_name: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority: Mapped[int] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM)


    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="tasks")