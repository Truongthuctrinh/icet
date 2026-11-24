from fastapi import Request

from app.core.config import settings

_TRUSTED = {ip.strip() for ip in settings.TRUSTED_PROXIES.split(",") if ip.strip()}


def get_client_ip(request: Request) -> str:
    """IP thật của người dùng.

    Khi chạy sau proxy (Vite dev server, nginx), request.client.host là IP của proxy;
    IP thật nằm ở header X-Forwarded-For. Chỉ tin header này khi request đến từ proxy
    nằm trong TRUSTED_PROXIES — nếu không, kẻ gian tự đặt header để giả IP.
    """
    direct = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and direct in _TRUSTED:
        return forwarded.split(",")[0].strip()
    return direct
