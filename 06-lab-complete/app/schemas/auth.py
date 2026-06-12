from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
    confirm_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True
