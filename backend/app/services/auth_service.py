from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import DUMMY_HASH, hash_password, verify_password
from app.models import User
from app.schemas.user import UserCreate


def register_user(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    existing = db.scalar(
        select(User).where(or_(User.username == data.username, User.email == email))
    )
    if existing:
        field = "Username" if existing.username == data.username else "Email"
        raise ValueError(f"{field} đã được sử dụng")

    user = User(
        username=data.username,
        email=email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    """Đăng nhập bằng username hoặc email."""
    user = db.scalar(
        select(User).where(or_(User.username == identifier, User.email == identifier.lower()))
    )
    if user is None:
        verify_password(password, DUMMY_HASH)  # chống dò user qua thời gian phản hồi
        return None
    if not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user
