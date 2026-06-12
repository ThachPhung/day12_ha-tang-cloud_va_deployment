from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=100)
    role: str = "user"


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None


class UserListItem(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    deck_count: int = 0
    card_count: int = 0

    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8)
