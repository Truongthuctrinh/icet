"""Lưu / xoá file ảnh trong thư mục media. Đường dẫn công khai dạng /media/<loại>/<mã>.webp"""
import logging
import re
import uuid

from app.core.config import settings
from app.core.images import process_image

logger = logging.getLogger("icet.media")

FOLDERS = {"cover": "covers", "avatar": "avatars"}
URL_PATTERN = re.compile(r"^/media/(covers|avatars)/([0-9a-f]{32})\.webp$")


def save_image(raw: bytes, kind: str) -> str:
    data = process_image(raw, kind)  # ImageError nếu ảnh không hợp lệ
    folder = settings.media_path / FOLDERS[kind]
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.webp"  # tên ngẫu nhiên: không đoán được, không trùng, không dùng tên người dùng đặt
    (folder / name).write_bytes(data)
    return f"/media/{FOLDERS[kind]}/{name}"


def delete_image(url: str | None) -> None:
    """Chỉ xoá file đúng mẫu do chính hệ thống tạo (chặn kiểu ../../etc/passwd)."""
    if not url:
        return
    match = URL_PATTERN.match(url)
    if not match:
        return
    path = settings.media_path / match.group(1) / f"{match.group(2)}.webp"
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Không xoá được ảnh %s", path)
