"""So sánh theo nghĩa (embedding): bắt văn bản bị viết lại mà MinHash bỏ sót."""
import time

import numpy as np

import app.services.plagiarism_service as plagiarism_module
from app.core.config import settings
from app.core.minhash import jaccard, shingles
from tests.conftest import make_admin, register_and_login
from tests.fake_embedder import FakeEmbedder
from tests.test_core_flow import make_chapter, make_story
from tests.test_plagiarism import ORIGINAL, OWN

# Viết lại 4 đoạn của ORIGINAL: đổi từ đồng nghĩa, đảo vế câu -> gần như không còn chuỗi 5 chữ nào trùng
PARAPHRASE = [
    "Đã mười năm kể từ trận lụt, Lam mới trở lại phố huyện cũ lần đầu. Hồ nước yên đến nỗi nàng thấy được mây lướt ngang mái ngói trường tiểu học.",
    "Ông chèo thuyền dặn nàng chớ có xuống nước lúc hoàng hôn. Theo ông, lúc nắng nghiêng về phía đồi, hồ chuyển sắc và những kẻ dưới ấy tỉnh dậy.",
    "Lam mỉm cười, thắt lại kính lặn. Nàng chẳng tin ma quỷ gì cả. Nàng chỉ mong tìm được cái rương thiếc má từng vùi dưới gốc khế trước nhà.",
    "Nước buốt hơn nàng nghĩ. Xuống sâu chừng năm mét, ánh sáng nhạt đi thành xanh ngọc, kế đó là xanh lục, rồi một sắc màu chẳng ai đặt tên.",
]
UNRELATED = [
    "Chợ phiên sáng chủ nhật đông nghịt người, tiếng rao hàng lẫn tiếng gà vịt inh ỏi khắp con dốc dẫn lên đình làng.",
    "Bà nội gói bánh chưng từ chiều hai mươi tám, lá dong xanh mướt xếp chồng trên chiếc nong tre đặt giữa sân gạch.",
    "Thằng Tí chạy ù ra đồng thả diều, sợi dây gai căng phần phật trong gió nồm, con diều sáo kêu vi vu suốt buổi trưa.",
]


def _ids(client, headers, story_id):
    return [c["id"] for c in client.get(f"/api/stories/{story_id}/chapters/manage", headers=headers).json()]


def test_fake_embedder_sanity():
    emb = FakeEmbedder().embed([ORIGINAL[1], PARAPHRASE[1], UNRELATED[0]])
    assert emb[0] @ emb[1] >= 0.85  # viết lại -> gần nhau
    assert emb[0] @ emb[2] < 0.5  # khác chủ đề -> xa nhau
    # Và MinHash thì KHÔNG nhận ra 2 đoạn viết lại này
    assert jaccard(shingles(ORIGINAL[1]), shingles(PARAPHRASE[1])) < 0.5


def test_paraphrase_caught_only_with_embedding(client, monkeypatch):
    monkeypatch.setattr(settings, "SEMANTIC_THRESHOLD", 0.85)
    admin = make_admin(client)
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "vietlai")
    c = register_and_login(client, "khac")

    sa = make_story(client, a, "Hồ ký ức")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    time.sleep(1.1)
    sb = make_story(client, b, "Bản viết lại")
    make_chapter(client, b, sb["id"], content="\n".join(OWN + PARAPHRASE))
    sc = make_story(client, c, "Chuyện làng")
    make_chapter(client, c, sc["id"], content="\n".join(UNRELATED))

    # Chỉ MinHash (như khi không có worker): không phát hiện được
    assert client.get("/api/plagiarism/reports", headers=admin).json() == []

    # Worker có model: kiểm tra lại theo thứ tự đăng
    fake = FakeEmbedder()
    for chapter_id in _ids(client, a, sa["id"]) + _ids(client, b, sb["id"]) + _ids(client, c, sc["id"]):
        plagiarism_module.run_check_in_background(chapter_id, fake)

    reports = client.get("/api/plagiarism/reports", headers=admin).json()
    assert len(reports) == 1
    rep = reports[0]
    assert rep["suspect"]["author_username"] == "vietlai"
    assert rep["source"]["author_username"] == "tacgia"
    assert rep["matched_count"] == 4
    assert {m["method"] for m in rep["matches"]} == {"semantic"}
    # Cặp đoạn ghép đúng: đoạn viết lại i <-> đoạn gốc i
    assert [(m["suspect_index"] - len(OWN), m["source_index"]) for m in rep["matches"]] == [(i, i) for i in range(4)]
    assert all(m["similarity"] >= 0.85 for m in rep["matches"])


def test_exact_copy_keeps_minhash_label(client):
    admin = make_admin(client)
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "daovan")
    sa = make_story(client, a, "Hồ ký ức")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    time.sleep(1.1)
    sb = make_story(client, b, "Bản chép")
    make_chapter(client, b, sb["id"], content="\n".join(OWN + ORIGINAL[1:4]))

    fake = FakeEmbedder()
    db = plagiarism_module.SessionLocal()
    try:
        result = plagiarism_module.reindex_all(db, fake)
    finally:
        db.close()
    assert result["reports"] == 1
    rep = client.get("/api/plagiarism/reports", headers=admin).json()[0]
    # Chép nguyên văn: cả MinHash lẫn embedding đều bắt, nhãn giữ là "minhash" (bằng chứng mạnh hơn)
    assert {m["method"] for m in rep["matches"]} == {"minhash"}


def test_semantic_threshold_respected(client, monkeypatch):
    """Đặt ngưỡng cao hơn độ giống thực tế -> không cảnh báo."""
    monkeypatch.setattr(settings, "SEMANTIC_THRESHOLD", 0.999)
    admin = make_admin(client)
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "vietlai")
    sa = make_story(client, a, "Hồ ký ức")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    time.sleep(1.1)
    sb = make_story(client, b, "Bản viết lại")
    make_chapter(client, b, sb["id"], content="\n".join(OWN + PARAPHRASE))
    db = plagiarism_module.SessionLocal()
    try:
        plagiarism_module.reindex_all(db, FakeEmbedder())
    finally:
        db.close()
    assert client.get("/api/plagiarism/reports", headers=admin).json() == []


def test_embeddings_stored_and_cleared(client):
    from app.models import ParagraphEmbedding
    from sqlalchemy import func, select

    a = register_and_login(client, "tacgia")
    sa = make_story(client, a, "Hồ ký ức")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    (cid,) = _ids(client, a, sa["id"])
    fake = FakeEmbedder()
    plagiarism_module.run_check_in_background(cid, fake)
    plagiarism_module.run_check_in_background(cid, fake)  # chạy lại không nhân đôi dữ liệu
    db = plagiarism_module.SessionLocal()
    try:
        rows = db.scalars(select(ParagraphEmbedding).where(ParagraphEmbedding.chapter_id == cid)).all()
        assert len(rows) == len(ORIGINAL)
        vec = np.asarray(rows[0].embedding)
        assert vec.shape == (384,) and abs(np.linalg.norm(vec) - 1) < 1e-3
    finally:
        db.close()
