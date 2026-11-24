"""Rate limit kiểu "cửa sổ cố định" bằng Redis.

Mỗi (hành động, user/IP) có 1 bộ đếm trong Redis, tự hết hạn sau `window` giây.
Vượt ngưỡng -> HTTP 429 + header Retry-After, và ghi nhận 1 lần vi phạm.
"""
import logging

from fastapi import Depends, HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.deps import get_current_user
from app.core.redis_client import redis_client
from app.models import User

logger = logging.getLogger("icet.rate_limit")

MESSAGES = {
    "open_chapter": "Bạn mở chương quá nhanh. Đợi {s} giây rồi thử lại.",
    "paragraphs": "Bạn tải nội dung quá nhanh. Đợi {s} giây rồi thử lại.",
    "login": "Đăng nhập sai quá nhiều lần. Đợi {s} giây rồi thử lại.",
    "comment": "Bạn bình luận quá nhanh. Đợi {s} giây rồi thử lại.",
}


def hit(key: str, limit: int, window: int) -> tuple[bool, int]:
    """Tăng bộ đếm. Trả về (được phép?, số giây phải chờ nếu bị chặn)."""
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window, nx=True)  # chỉ đặt hạn ở lần đếm đầu tiên của cửa sổ
    count, _ = pipe.execute()
    if count <= limit:
        return True, 0
    return False, max(redis_client.ttl(key), 1)


def _enforce(scope: str, subject: str, limit: int, window: int) -> None:
    try:
        allowed, retry_after = hit(f"rl:{scope}:{subject}", limit, window)
    except RedisError:
        # Redis lỗi thì cho qua (fail-open) để web không sập theo, nhưng ghi log
        logger.exception("Redis không phản hồi, bỏ qua rate limit %s", scope)
        return
    if allowed:
        return

    # Ghi nhận vi phạm: admin xem các key violations:* để phát hiện bot
    try:
        redis_client.incr(f"violations:{subject}")
        redis_client.incr(f"violations:{subject}:{scope}")
    except RedisError:
        pass
    logger.warning("Rate limit %s bị vượt bởi %s", scope, subject)

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=MESSAGES.get(scope, "Quá nhiều yêu cầu. Đợi {s} giây.").format(s=retry_after),
        headers={"Retry-After": str(retry_after)},
    )


def limit_by_user(scope: str, limit: int, window: int):
    """Dependency: giới hạn theo user đang đăng nhập."""

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        _enforce(scope, f"user:{current_user.id}", limit, window)

    return dependency


def limit_by_ip(scope: str, limit: int, window: int):
    """Dependency: giới hạn theo địa chỉ IP (dùng khi chưa đăng nhập, như form login)."""

    def dependency(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        _enforce(scope, f"ip:{ip}", limit, window)

    return dependency
