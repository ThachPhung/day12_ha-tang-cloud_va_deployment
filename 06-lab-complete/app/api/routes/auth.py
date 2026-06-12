from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, change_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    if not data.username.strip():
        raise HTTPException(status_code=400, detail="Tên đăng nhập không được để trống")
    if not data.password:
        raise HTTPException(status_code=400, detail="Mật khẩu không được để trống")

    user = authenticate_user(db, data.username.strip(), data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout():
    return {"message": "Đăng xuất thành công"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.put("/change-password")
def change_user_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    error = change_password(db, current_user, data.current_password, data.new_password, data.confirm_password)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Đổi mật khẩu thành công"}
