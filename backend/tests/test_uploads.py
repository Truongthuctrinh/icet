"""Tải ảnh bìa truyện + ảnh đại diện."""
import io

from PIL import Image

from app.core.config import settings
from tests.conftest import register_and_login
from tests.test_core_flow import make_story


def image_bytes(fmt="PNG", size=(800, 600), color=(200, 60, 60), exif_gps=False) -> bytes:
    img = Image.new("RGB", size, color)
    out = io.BytesIO()
    kwargs = {}
    if exif_gps:
        exif = Image.Exif()
        exif[0x010F] = "Điện thoại bí mật"  # Make
        exif[0x8825] = {2: (10.0, 46.0, 30.0)}  # GPSInfo: vĩ độ
        kwargs["exif"] = exif
    img.save(out, format=fmt, **kwargs)
    return out.getvalue()


def upload(client, url, headers, data, name="anh.png", ctype="image/png"):
    return client.put(url, files={"file": (name, data, ctype)}, headers=headers)


def media_file(url: str):
    return settings.media_path / url.removeprefix("/media/")


def test_cover_upload_resized_and_exif_stripped(client):
    a = register_and_login(client, "tacgia")
    story = make_story(client, a, "Hồ ký ức")
    r = upload(client, f"/api/stories/{story['id']}/cover", a, image_bytes("JPEG", (1200, 900), exif_gps=True), "bia.jpg", "image/jpeg")
    assert r.status_code == 200, r.text
    url = r.json()["cover_url"]
    assert url.startswith("/media/covers/") and url.endswith(".webp")

    served = client.get(url)
    assert served.status_code == 200
    img = Image.open(io.BytesIO(served.content))
    assert img.format == "WEBP" and img.size == (600, 900)
    assert len(img.getexif()) == 0  # không còn GPS / tên máy

    # Ảnh mới thay ảnh cũ -> file cũ bị xoá
    r2 = upload(client, f"/api/stories/{story['id']}/cover", a, image_bytes())
    assert not media_file(url).exists()
    assert media_file(r2.json()["cover_url"]).exists()
    # Danh sách truyện của tác giả trả về cover_url
    assert client.get("/api/stories/mine", headers=a).json()[0]["cover_url"] == r2.json()["cover_url"]

    # Gỡ ảnh bìa
    r3 = client.delete(f"/api/stories/{story['id']}/cover", headers=a)
    assert r3.json()["cover_url"] is None and not media_file(r2.json()["cover_url"]).exists()


def test_cover_only_by_owner(client):
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "nguoikhac")
    story = make_story(client, a, "Hồ ký ức")
    assert upload(client, f"/api/stories/{story['id']}/cover", b, image_bytes()).status_code == 403
    assert client.put(f"/api/stories/{story['id']}/cover", files={"file": ("a.png", image_bytes(), "image/png")}).status_code == 401


def test_reject_fake_and_oversized_images(client):
    a = register_and_login(client, "tacgia")
    story = make_story(client, a, "Hồ ký ức")
    url = f"/api/stories/{story['id']}/cover"
    # File HTML đổi đuôi thành .png
    r = upload(client, url, a, b"<html><script>alert(1)</script></html>", "hack.png")
    assert r.status_code == 422 and "không phải ảnh" in r.json()["detail"]
    # GIF thật nhưng không thuộc định dạng cho phép
    assert upload(client, url, a, image_bytes("GIF"), "a.gif", "image/gif").status_code == 422
    # Quá dung lượng
    big = b"\x89PNG" + b"0" * (settings.MAX_UPLOAD_MB * 1024 * 1024 + 10)
    assert upload(client, url, a, big).status_code == 413
    # Bom giải nén: ảnh siêu lớn về số điểm ảnh
    bomb = image_bytes("PNG", (8000, 8000), (0, 0, 0))
    assert upload(client, url, a, bomb).status_code == 422


def test_avatar_shown_everywhere(client):
    a = register_and_login(client, "tacgia")
    r = upload(client, "/api/users/me/avatar", a, image_bytes("PNG", (300, 500)))
    assert r.status_code == 200
    avatar = r.json()["avatar_url"]
    assert Image.open(io.BytesIO(client.get(avatar).content)).size == (256, 256)
    assert client.get("/api/auth/me", headers=a).json()["avatar_url"] == avatar
    assert client.get("/api/users/tacgia").json()["avatar_url"] == avatar
    make_story(client, a, "Hồ ký ức")
    assert client.get("/api/stories/mine", headers=a).json()[0]["author"]["avatar_url"] == avatar

    r = client.delete("/api/users/me/avatar", headers=a)
    assert r.json()["avatar_url"] is None and not media_file(avatar).exists()


def test_upload_rate_limited(client):
    a = register_and_login(client, "tacgia")
    data = image_bytes(size=(50, 50))
    codes = [upload(client, "/api/users/me/avatar", a, data).status_code for _ in range(settings.RATE_UPLOAD_PER_MIN + 1)]
    assert codes[:-1] == [200] * settings.RATE_UPLOAD_PER_MIN and codes[-1] == 429


def test_deleting_story_removes_cover(client):
    a = register_and_login(client, "tacgia")
    story = make_story(client, a, "Hồ ký ức")
    url = upload(client, f"/api/stories/{story['id']}/cover", a, image_bytes()).json()["cover_url"]
    assert client.delete(f"/api/stories/{story['id']}", headers=a).status_code == 204
    assert not media_file(url).exists()
