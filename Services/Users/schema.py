from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    name: str
    email: Optional[str] = Field(default=None)
    password: str

    @field_validator("email")
    def email_to_lower(cls, v):
        if v is not None:
            return v.lower()
        return v


class UserRead(BaseModel):
    name: str
    email: Optional[str] = Field(default=None)
    active: bool