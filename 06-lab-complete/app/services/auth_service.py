from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole, UserSettings


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return user


def change_password(db: Session, user: User, current: str, new: str, confirm: str) -> str | None:
    if not verify_password(current, user.password_hash):
        return "Mật khẩu hiện tại không đúng"
    if new != confirm:
        return "Mật khẩu xác nhận không khớp"
    if len(new) < 8:
        return "Mật khẩu mới phải có ít nhất 8 ký tự"
    if verify_password(new, user.password_hash):
        return "Mật khẩu mới không được giống mật khẩu cũ"
    user.password_hash = get_password_hash(new)
    db.commit()
    return None


def create_user_settings(db: Session, user_id: int) -> UserSettings:
    settings = UserSettings(user_id=user_id)
    db.add(settings)
    db.commit()
    return settings


def count_non_admin_users(db: Session) -> int:
    return db.query(User).filter(User.role == UserRole.user).count()
