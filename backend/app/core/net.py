import ipaddress

from fastapi import Request

from app.core.config import settings


def _parse_trusted(raw: str):
    """TRUSTED_PROXIES nhận IP lẻ (127.0.0.1), dải IP (172.16.0.0/12 — mạng nội bộ Docker)
    hoặc tên máy (testclient, dùng khi chạy test)."""
    networks, names = [], set()
    for item in (x.strip() for x in raw.split(",")):
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            names.add(item)
    return networks, names


_NETWORKS, _NAMES = _parse_trusted(settings.TRUSTED_PROXIES)


def is_trusted_proxy(host: str) -> bool:
    if host in _NAMES:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in net for net in _NETWORKS)


def get_client_ip(request: Request) -> str:
    """IP thật của người dùng.

    Khi chạy sau proxy (Vite dev server, nginx), request.client.host là IP của proxy;
    IP thật nằm ở header X-Forwarded-For. Chỉ tin header này khi request đến từ proxy
    nằm trong TRUSTED_PROXIES — nếu không, kẻ gian tự đặt header để giả IP.
    """
    direct = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and is_trusted_proxy(direct):
        return forwarded.split(",")[0].strip()
    return direct
