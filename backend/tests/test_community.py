"""Đợt 1: thể loại, tìm kiếm, theo dõi + thông báo, bình luận, đánh giá, hồ sơ."""
from tests.conftest import register_and_login
from tests.test_core_flow import make_chapter, make_story


def genre_id(client, slug):
    return next(g["id"] for g in client.get("/api/genres").json() if g["slug"] == slug)


def test_genres_seeded_and_search_filters(client):
    a = register_and_login(client, "tacgia", "Bút Danh Mây")
    assert len(client.get("/api/genres").json()) == 12
    kd, nt = genre_id(client, "kinh-di"), genre_id(client, "ngon-tinh")
    make_story(client, a, "Ngôi nhà cuối phố", genre_ids=[kd])
    make_story(client, a, "Mùa hạ năm ấy", genre_ids=[nt])
    make_story(client, a, "Bản nháp bí mật", publish=False, genre_ids=[kd])

    titles = lambda url: [s["title"] for s in client.get(url).json()]
    assert titles("/api/stories?genre=kinh-di") == ["Ngôi nhà cuối phố"]
    assert titles("/api/stories?q=mùa hạ") == ["Mùa hạ năm ấy"]
    assert len(titles("/api/stories?q=Bút Danh")) == 2  # tìm theo tên tác giả
    assert client.get("/api/stories").json()[0]["genres"][0]["name"] in ("Kinh dị", "Ngôn tình")
    assert client.post("/api/stories", json={"title": "x", "genre_ids": [999]}, headers=a).status_code == 422


def test_follow_and_new_chapter_notifications(client):
    a = register_and_login(client, "tacgia")
    r = register_and_login(client, "docgia")
    story = make_story(client, a)
    sid = story["id"]

    assert client.post(f"/api/stories/{sid}/follow", headers=r).json() == {"is_following": True, "follower_count": 1}
    client.post(f"/api/stories/{sid}/follow", headers=r)  # bấm 2 lần không bị đếm đôi
    assert client.get(f"/api/stories/{sid}", headers=r).json()["is_following"] is True
    assert client.get(f"/api/stories/{sid}").json()["follower_count"] == 1

    draft = make_chapter(client, a, sid, publish=False, title="Bản nháp")
    assert client.get("/api/notifications/unread-count", headers=r).json()["count"] == 0

    client.patch(f"/api/stories/{sid}/chapters/{draft['id']}", json={"is_published": True}, headers=a)
    notes = client.get("/api/notifications", headers=r).json()
    assert len(notes) == 1 and notes[0]["kind"] == "new_chapter"
    assert notes[0]["link"] == f"/truyen/{sid}/chuong/{draft['id']}"

    # Ẩn rồi xuất bản lại: KHÔNG gửi thông báo lần 2
    client.patch(f"/api/stories/{sid}/chapters/{draft['id']}", json={"is_published": False}, headers=a)
    client.patch(f"/api/stories/{sid}/chapters/{draft['id']}", json={"is_published": True}, headers=a)
    assert client.get("/api/notifications/unread-count", headers=r).json()["count"] == 1

    client.post(f"/api/notifications/{notes[0]['id']}/read", headers=r)
    assert client.get("/api/notifications/unread-count", headers=r).json()["count"] == 0
    assert [s["id"] for s in client.get("/api/me/following", headers=r).json()] == [sid]

    client.delete(f"/api/stories/{sid}/follow", headers=r)
    assert client.get(f"/api/stories/{sid}").json()["follower_count"] == 0


def test_comments_replies_and_moderation(client):
    a = register_and_login(client, "tacgia")
    r1 = register_and_login(client, "docgia1")
    r2 = register_and_login(client, "docgia2")
    story = make_story(client, a)
    ch = make_chapter(client, a, story["id"])
    url = f"/api/stories/{story['id']}/chapters/{ch['id']}/comments"

    assert client.post(url, json={"content": "Hay quá!"}, headers=r1).status_code == 201
    root = client.get(url).json()[0]
    client.post(url, json={"content": "Cảm ơn bạn", "parent_id": root["id"]}, headers=a)
    reply = client.get(url).json()[0]["replies"][0]
    # Trả lời của trả lời -> vẫn gắn vào bình luận gốc (1 cấp)
    client.post(url, json={"content": "Mình cũng thấy vậy", "parent_id": reply["id"]}, headers=r2)
    tree = client.get(url).json()
    assert len(tree) == 1 and len(tree[0]["replies"]) == 2
    assert tree[0]["replies"][0]["is_story_author"] is True

    kinds = lambda h: sorted(n["kind"] for n in client.get("/api/notifications", headers=h).json())
    assert kinds(a) == ["comment", "comment"]  # docgia1 bình luận + docgia2 trả lời
    assert kinds(r1) == ["reply", "reply"]  # tác giả + docgia2 trả lời bình luận của docgia1

    # Sửa: chỉ chủ bình luận
    assert client.patch(f"{url}/{root['id']}", json={"content": "Sửa"}, headers=r2).status_code == 403
    assert client.patch(f"{url}/{root['id']}", json={"content": "Hay thật sự!"}, headers=r1).status_code == 200
    # Xoá: tác giả truyện được xoá (kiểm duyệt), người lạ thì không
    assert client.delete(f"{url}/{root['id']}", headers=r2).status_code == 403
    tree = client.delete(f"{url}/{root['id']}", headers=a).json()
    assert tree[0]["is_deleted"] and tree[0]["content"] == "" and len(tree[0]["replies"]) == 2


def test_comment_rate_limit(client):
    a = register_and_login(client, "tacgia")
    spam = register_and_login(client, "spam")
    story = make_story(client, a)
    ch = make_chapter(client, a, story["id"])
    url = f"/api/stories/{story['id']}/chapters/{ch['id']}/comments"
    codes = [client.post(url, json={"content": f"spam {i}"}, headers=spam).status_code for i in range(7)]
    assert codes == [201] * 5 + [429, 429]


def test_ratings(client):
    a = register_and_login(client, "tacgia")
    r1 = register_and_login(client, "docgia1")
    r2 = register_and_login(client, "docgia2")
    sid = make_story(client, a)["id"]
    url = f"/api/stories/{sid}/ratings"

    assert client.put(f"{url}/me", json={"score": 5}, headers=a).status_code == 403  # tự chấm
    assert client.put(f"{url}/me", json={"score": 6}, headers=r1).status_code == 422
    client.put(f"{url}/me", json={"score": 5, "review": "Tuyệt"}, headers=r1)
    client.put(f"{url}/me", json={"score": 2}, headers=r2)
    client.put(f"{url}/me", json={"score": 4}, headers=r2)  # sửa lại, không tạo bản mới
    summary = client.get(url).json()
    assert summary["rating_count"] == 2 and summary["rating_avg"] == 4.5
    assert summary["distribution"]["5"] == 1 and summary["distribution"]["4"] == 1
    assert client.get(f"/api/stories/{sid}", headers=r2).json()["my_rating"]["score"] == 4

    client.delete(f"{url}/me", headers=r2)
    assert client.get(f"/api/stories/{sid}").json()["rating_avg"] == 5.0
    assert [s["title"] for s in client.get("/api/stories?sort=rating").json()][0] == "Truyện thử"


def test_profile(client):
    a = register_and_login(client, "tacgia", "Mây Trắng")
    make_story(client, a, "Truyện công khai")
    make_story(client, a, "Bản nháp", publish=False)
    p = client.get("/api/users/tacgia").json()
    assert p["display_name"] == "Mây Trắng" and p["story_count"] == 1
    assert client.get("/api/users/khongco").status_code == 404
