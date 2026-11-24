"""Các luồng đã có từ trước: auth, truyện, chương, đọc theo đoạn, watermark, rate limit."""
from app.core.watermark import extract_session_ids, strip_marks
from tests.conftest import register_and_login

TEXT = "\n".join(f"Đoạn văn số {i} kể về chuyến đi dài qua những cánh đồng lúa chín vàng." for i in range(1, 13))


def make_story(client, headers, title="Truyện thử", publish=True, genre_ids=None):
    r = client.post("/api/stories", json={"title": title, "genre_ids": genre_ids or []}, headers=headers)
    assert r.status_code == 201, f"Tạo truyện lỗi {r.status_code}: {r.text}"
    story = r.json()
    if publish:
        client.patch(f"/api/stories/{story['id']}", json={"is_published": True}, headers=headers)
    return story


def make_chapter(client, headers, story_id, content=TEXT, publish=True, title="Chương"):
    r = client.post(
        f"/api/stories/{story_id}/chapters",
        json={"title": title, "content": content, "is_published": publish},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_auth_and_token_types(client):
    h = register_and_login(client, "han")
    assert client.get("/api/auth/me", headers=h).json()["username"] == "han"
    assert client.post("/api/auth/register", json={
        "username": "han", "email": "x@y.vn", "password": "matkhau123", "display_name": "X"}).status_code == 409
    assert client.post("/api/auth/login", data={"username": "han", "password": "sai"}).status_code == 401


def test_owner_permissions_and_drafts(client):
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "khach")
    story = make_story(client, a, publish=False)
    assert client.get(f"/api/stories/{story['id']}").status_code == 404  # bản nháp: người ngoài không thấy
    assert client.patch(f"/api/stories/{story['id']}", json={"title": "x"}, headers=b).status_code == 403
    assert len(client.get("/api/stories/mine", headers=a).json()) == 1


def test_reading_flow_watermark_and_trace(client):
    a = register_and_login(client, "tacgia")
    r = register_and_login(client, "docgia")
    story = make_story(client, a)
    ch = make_chapter(client, a, story["id"])
    base = f"/api/stories/{story['id']}/chapters/{ch['id']}"

    s = client.post(f"{base}/session", headers=r).json()
    assert s["total_paragraphs"] == 12 and "content" not in s["chapter"]
    token = s["session_token"]

    # Vé đọc không dùng thay access token được
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401

    batch = client.get(f"{base}/paragraphs?start=0&limit=10", headers={**r, "X-Read-Token": token}).json()
    assert len(batch["paragraphs"]) == 10 and batch["has_more"]
    leaked = "\n".join(p["text"] for p in batch["paragraphs"])
    assert strip_marks(leaked).startswith("Đoạn văn số 1")
    assert extract_session_ids(leaked)[1] != []

    # Người khác dùng vé của docgia -> 403
    other = register_and_login(client, "nguoikhac")
    assert client.get(f"{base}/paragraphs", headers={**other, "X-Read-Token": token}).status_code == 403

    # Tác giả truy vết ra đúng người đọc
    t = client.post("/api/trace", json={"text": leaked}, headers=a).json()
    assert t["matches"][0]["reader_username"] == "docgia"
    # Người không phải tác giả không xem được chi tiết
    assert client.post("/api/trace", json={"text": leaked}, headers=other).json()["hidden_matches"] == 1


def test_rate_limit_open_chapter(client):
    a = register_and_login(client, "tacgia")
    bot = register_and_login(client, "bot")
    story = make_story(client, a)
    ch = make_chapter(client, a, story["id"])
    codes = [
        client.post(f"/api/stories/{story['id']}/chapters/{ch['id']}/session", headers=bot).status_code
        for _ in range(12)
    ]
    assert codes == [201] * 10 + [429, 429]


def test_login_lockout_counts_only_failures(client):
    register_and_login(client, "han")
    for _ in range(3):
        client.post("/api/auth/login", data={"username": "han", "password": "matkhau123"})
    codes = [client.post("/api/auth/login", data={"username": "han", "password": "sai"}).status_code for _ in range(7)]
    assert codes == [401] * 5 + [429, 429]
