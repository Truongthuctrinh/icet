"""Đợt 2: lớp chắn (bot AI, honeypot, header), trang quản trị, khoá chương đạo văn."""
import time

from tests.conftest import make_admin, register_and_login
from tests.test_core_flow import make_chapter, make_story
from tests.test_plagiarism import ORIGINAL, OWN

GPTBOT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)"


def test_security_headers_and_robots(client):
    r = client.get("/api/stories")
    assert r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    robots = client.get("/robots.txt").text
    assert "User-agent: GPTBot\nDisallow: /" in robots and "Disallow: /api/export/all-stories" in robots


def test_ai_crawler_blocked(client):
    admin = make_admin(client)  # tạo trước: đăng nhập trong test có xoá Redis giả
    assert client.get("/api/stories", headers={"User-Agent": GPTBOT}).status_code == 403
    assert client.get("/api/stories", headers={"User-Agent": "CCBot/2.0"}).status_code == 403
    assert client.get("/api/stories").status_code == 200  # trình duyệt bình thường vẫn vào được
    sec = client.get("/api/admin/security", headers=admin).json()
    assert sec["bot_hits"] == {"GPTBot": 1, "CCBot": 1}


def test_honeypot_bans_only_that_ip(client):
    bot_ip = {"X-Forwarded-For": "10.6.6.6"}
    admin = make_admin(client)
    user = register_and_login(client, "docgia")
    assert client.get("/api/export/all-stories", headers={**bot_ip, **user}).status_code == 403
    # IP dính bẫy bị chặn mọi API
    assert client.get("/api/stories", headers=bot_ip).status_code == 403
    # IP khác không ảnh hưởng
    assert client.get("/api/stories", headers={"X-Forwarded-For": "10.1.1.1"}).status_code == 200

    sec = client.get("/api/admin/security", headers=admin).json()
    assert sec["bans"][0]["ip"] == "10.6.6.6" and sec["bans"][0]["expires_in"] > 0
    assert sec["honeypot_log"][0]["user_id"] is not None
    assert any(v["subject"].startswith("user:") and v["by_scope"].get("honeypot") == 1 for v in sec["violations"])

    assert client.delete("/api/admin/security/bans/10.6.6.6", headers=admin).status_code == 204
    assert client.get("/api/stories", headers=bot_ip).status_code == 200


def test_forwarded_header_not_trusted_from_outside(client):
    """Kẻ gian tự gửi X-Forwarded-For (không qua proxy tin cậy) thì không giả được IP."""
    from starlette.requests import Request

    from app.core.net import get_client_ip

    scope = {"type": "http", "client": ("203.0.113.9", 5000), "headers": [(b"x-forwarded-for", b"1.2.3.4")]}
    assert get_client_ip(Request(scope)) == "203.0.113.9"


def test_admin_requires_role_and_overview(client):
    user = register_and_login(client, "docgia")
    assert client.get("/api/admin/overview", headers=user).status_code == 403
    admin = make_admin(client)
    a = register_and_login(client, "tacgia")
    story = make_story(client, a)
    make_chapter(client, a, story["id"])
    ov = client.get("/api/admin/overview", headers=admin).json()
    assert ov["users"] == 3 and ov["stories_published"] == 1 and ov["chapters_published"] == 1


def test_lock_user(client):
    admin = make_admin(client)
    victim = register_and_login(client, "spammer")
    users = client.get("/api/admin/users?q=spammer", headers=admin).json()
    uid = users[0]["id"]

    assert client.patch(f"/api/admin/users/{uid}", json={"is_active": False}, headers=admin).json()["is_active"] is False
    assert client.get("/api/auth/me", headers=victim).status_code == 401  # token cũ hết tác dụng
    r = client.post("/api/auth/login", data={"username": "spammer", "password": "matkhau123"})
    assert r.status_code == 403 and "khoá" in r.json()["detail"]
    # Sai mật khẩu thì vẫn chỉ báo "sai" -> không lộ tài khoản bị khoá
    assert client.post("/api/auth/login", data={"username": "spammer", "password": "sai"}).status_code == 401

    me_id = client.get("/api/auth/me", headers=admin).json()["id"]
    assert client.patch(f"/api/admin/users/{me_id}", json={"is_active": False}, headers=admin).status_code == 400


def test_confirmed_plagiarism_hides_and_locks_chapter(client):
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "daovan")
    admin = make_admin(client)
    sa = make_story(client, a, "Bản gốc")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    time.sleep(1.1)
    sb = make_story(client, b, "Bản chép")
    ch = make_chapter(client, b, sb["id"], content="\n".join(OWN + ORIGINAL[1:4]))

    rep = client.get("/api/plagiarism/reports", headers=admin).json()[0]
    client.patch(f"/api/plagiarism/reports/{rep['id']}", json={"status": "confirmed"}, headers=admin)

    # Chương bị ẩn khỏi mục lục công khai và bị đánh dấu khoá ở trang quản lý
    assert client.get(f"/api/stories/{sb['id']}/chapters").json() == []
    manage = client.get(f"/api/stories/{sb['id']}/chapters/manage", headers=b).json()
    assert manage[0]["is_locked"] is True and manage[0]["is_published"] is False
    # Tác giả không tự xuất bản lại được
    r = client.patch(f"/api/stories/{sb['id']}/chapters/{ch['id']}", json={"is_published": True}, headers=b)
    assert r.status_code == 422 and "xác nhận sao chép" in r.json()["detail"]
    assert "plagiarism_confirmed" in [n["kind"] for n in client.get("/api/notifications", headers=b).json()]

    # Admin đưa về "bỏ qua" -> tác giả xuất bản lại được
    client.patch(f"/api/plagiarism/reports/{rep['id']}", json={"status": "dismissed"}, headers=admin)
    r = client.patch(f"/api/stories/{sb['id']}/chapters/{ch['id']}", json={"is_published": True}, headers=b)
    assert r.status_code == 200
