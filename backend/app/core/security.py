from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hasher = PasswordHash.recommended()  # argon2
# Hash giả dùng khi user không tồn tại, để thời gian phản hồi giống nhau
DUMMY_HASH = password_hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)


# ---------- JWT dùng chung ----------

def _encode(payload: dict, minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {**payload, "iat": now, "exp": now + timedelta(minutes=minutes)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _decode(token: str, expected_type: str) -> dict | None:
    """Giải mã và CHỈ chấp nhận đúng loại token (access / read)."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            leeway=10,  # chấp nhận lệch đồng hồ tối đa 10 giây với hạn token (exp)
            # Không kiểm tra "iat": đồng hồ máy (nhất là WSL2) đôi khi nhảy vọt lên trước vài chục giây
            # lúc cấp token -> iat nằm ở "tương lai" -> token hợp lệ bị từ chối oan.
            # Hạn dùng vẫn do exp quyết định nên không ảnh hưởng bảo mật.
            options={"verify_iat": False},
        )
    except jwt.InvalidTokenError:
        return None
    if payload.get("typ") != expected_type:
        return None
    return payload


# ---------- Access token (đăng nhập) ----------

def create_access_token(user_id: int) -> str:
    return _encode({"typ": "access", "sub": str(user_id)}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def decode_access_token(token: str) -> int | None:
    payload = _decode(token, "access")
    if payload is None:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        return None


# ---------- Read token (vé đọc chương) ----------

def create_read_token(session_id: int, user_id: int, chapter_id: int) -> str:
    return _encode(
        {"typ": "read", "sub": str(user_id), "sid": session_id, "cid": chapter_id},
        settings.READ_TOKEN_EXPIRE_MINUTES,
    )


def decode_read_token(token: str) -> dict | None:
    return _decode(token, "read")
