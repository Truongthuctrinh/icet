"""Lớp chắn ở cửa ngõ, chạy TRƯỚC mọi API:
  1. IP đang bị cấm (do dính bẫy honeypot) -> 403.
  2. User-Agent là crawler AI đã biết (GPTBot, CCBot, ClaudeBot...) -> 403.
  3. Đường dẫn bẫy honeypot: người thật không bao giờ thấy -> ai gọi là bot -> cấm IP tạm thời.
  4. Gắn header bảo mật vào mọi phản hồi (chống nhúng iframe, chống đoán kiểu file, noai).
"""
import json
import logging
import re
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.net import get_client_ip
from app.core.redis_client import redis_client
from app.core.security import decode_access_token

logger = logging.getLogger("icet.shield")

AI_BOTS = re.compile(
    r"GPTBot|ChatGPT-User|OAI-SearchBot|CCBot|ClaudeBot|Claude-Web|anthropic-ai|"
    r"Google-Extended|PerplexityBot|Perplexity-User|Bytespider|Amazonbot|Applebot-Extended|"
    r"meta-externalagent|FacebookBot|Diffbot|ImagesiftBot|cohere-ai|YouBot|Omgilibot|"
    r"Timpibot|Scrapy|img2dataset",
    re.IGNORECASE,
)

# Đường dẫn bẫy: có trong link ẩn ở giao diện + bị cấm trong robots.txt.
# Người dùng thật không thấy link; bot "lịch sự" tuân theo robots.txt nên không vào;
# chỉ bot cào dữ liệu bất chấp mới gọi tới.
HONEYPOT_PATHS = {"/api/export/all-stories", "/api/stories/export"}

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",  # trình duyệt cũ
    "Content-Security-Policy": "frame-ancestors 'none'",  # không cho trang khác nhúng iframe
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "X-Robots-Tag": "noindex, noai, noimageai",  # API không cần được lập chỉ mục / dùng huấn luyện AI
}

LOG_SIZE = 100


def _push_log(key: str, entry: dict) -> None:
    redis_client.lpush(key, json.dumps(entry, ensure_ascii=False))
    redis_client.ltrim(key, 0, LOG_SIZE - 1)


def _user_id_from(request: Request) -> int | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return decode_access_token(auth[7:])
    return None


def _deny(detail: str) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": detail}, headers=SECURITY_HEADERS)


async def shield_middleware(request: Request, call_next):
    path = request.url.path
    ip = get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    try:
        # 1. IP bị cấm. Miễn cho đăng nhập + trang quản trị: nếu admin lỡ dùng chung IP với bot
        #    (vd. cùng chạy trên localhost khi dev) vẫn đăng nhập và gỡ cấm được.
        exempt = path.startswith(("/api/admin", "/api/auth"))
        if not exempt and redis_client.exists(f"ban:ip:{ip}"):
            return _deny("Địa chỉ IP của bạn đang bị tạm khoá vì có hành vi giống bot thu thập dữ liệu.")

        # 2. Crawler AI
        match = AI_BOTS.search(ua)
        if match and path != "/robots.txt":
            bot = match.group(0)
            redis_client.incr(f"bots:blocked:{bot}")
            _push_log("bots:log", {"bot": bot, "ip": ip, "path": path, "at": int(time.time())})
            return _deny("ICeT không cho phép bot thu thập nội dung để huấn luyện AI.")

        # 3. Bẫy honeypot
        if path in HONEYPOT_PATHS:
            user_id = _user_id_from(request)
            redis_client.setex(f"ban:ip:{ip}", settings.HONEYPOT_BAN_MINUTES * 60, "honeypot")
            if user_id:
                redis_client.incr(f"violations:user:{user_id}")
                redis_client.incr(f"violations:user:{user_id}:honeypot")
            _push_log(
                "honeypot:log",
                {"ip": ip, "user_id": user_id, "ua": ua[:200], "path": path, "at": int(time.time())},
            )
            logger.warning("Honeypot: IP %s (user %s) dính bẫy %s", ip, user_id, path)
            return _deny("Truy cập bị từ chối.")
    except RedisError:
        logger.exception("Redis lỗi, bỏ qua lớp chắn")  # fail-open: web không sập theo Redis

    response = await call_next(request)
    for key, value in SECURITY_HEADERS.items():
        response.headers.setdefault(key, value)
    return response
