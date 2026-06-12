from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.card import Card
from app.models.deck import Deck
from app.models.user import User, UserRole
from app.schemas.user import ResetPasswordRequest, UserCreate, UserListItem, UserUpdate
from app.services.auth_service import create_user_settings, count_non_admin_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserListItem])
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    users = db.query(User).order_by(User.created_at).all()
    result = []
    for u in users:
        deck_count = db.query(Deck).filter(Deck.owner_id == u.id, Deck.is_deleted == False).count()
        card_count = (
            db.query(Card)
            .join(Deck)
            .filter(Deck.owner_id == u.id, Card.is_deleted == False, Deck.is_deleted == False)
            .count()
        )
        result.append(UserListItem(
            id=u.id,
            username=u.username,
            email=u.email,
            display_name=u.display_name,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login_at=u.last_login_at,
            deck_count=deck_count,
            card_count=card_count,
        ))
    return result


@router.post("", response_model=UserListItem, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    if data.role != "admin" and count_non_admin_users(db) >= settings.MAX_USERS:
        raise HTTPException(status_code=400, detail=f"Tối đa {settings.MAX_USERS} tài khoản người học")

    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username đã tồn tại")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    user = User(
        username=data.username,
        email=data.email,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name,
        role=UserRole.admin if data.role == "admin" else UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    create_user_settings(db, user.id)

    return UserListItem(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.get("/{user_id}", response_model=UserListItem)
def get_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return UserListItem(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.patch("/{user_id}", response_model=UserListItem)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        user.email = data.email
    db.commit()
    db.refresh(user)
    return UserListItem(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Đặt lại mật khẩu thành công"}


@router.post("/{user_id}/lock")
def lock_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.is_active = False
    db.commit()
    return {"message": "Đã khóa tài khoản"}


@router.post("/{user_id}/unlock")
def unlock_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.is_active = True
    db.commit()
    return {"message": "Đã mở khóa tài khoản"}
