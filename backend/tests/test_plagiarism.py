"""Phát hiện đạo văn qua API thật (kiểm tra chạy nền sau khi lưu chương)."""
import time

from tests.conftest import register_and_login
from tests.test_core_flow import make_chapter, make_story

ORIGINAL = [
    "Mười năm sau trận lũ, lần đầu tiên Lam quay về thị trấn cũ. Mặt hồ phẳng lặng đến mức cô có thể nhìn thấy mây trôi qua mái ngói của trường tiểu học.",
    "Người lái đò bảo cô đừng lặn vào buổi chiều. Ông nói khi mặt trời chếch về phía núi, nước hồ đổi màu, và những ai ở dưới đó bắt đầu thức dậy.",
    "Lam cười, buộc lại dây kính lặn. Cô không tin chuyện ma quỷ. Cô chỉ muốn tìm lại chiếc hộp thiếc mẹ đã chôn dưới gốc cây khế trước nhà.",
    "Nước lạnh hơn cô tưởng. Ở độ sâu năm mét, ánh sáng mờ dần thành màu xanh ngọc, rồi xanh lục, rồi một thứ màu không có tên.",
    "Và rồi cô nghe thấy nó: tiếng chuông trường, ba hồi dài, đúng như những buổi sáng thứ hai năm cô mười tuổi khi cả lớp xếp hàng.",
]
OWN = [
    "Gió mùa đông bắc tràn về sớm hơn mọi năm. Trên con đường đất đỏ dẫn ra bến xe, Tuấn kéo chiếc vali cũ kỹ, bánh xe kêu lọc cọc.",
    "Bến xe vắng tanh. Chỉ có một bà cụ bán bánh mì ngồi co ro bên bếp than hồng, khói bay lên hòa vào màn sương dày đặc.",
]


def test_copy_detected_and_notified(client):
    a = register_and_login(client, "tacgia")
    b = register_and_login(client, "daovan")
    admin = register_and_login(client, "quantri")
    from app.models import User
    import app.main as m
    db = m.SessionLocal()
    db.query(User).filter_by(username="quantri").update({"role": "admin"}); db.commit(); db.close()

    sa = make_story(client, a, "Bản gốc")
    make_chapter(client, a, sa["id"], content="\n".join(ORIGINAL))
    time.sleep(1.1)
    sb = make_story(client, b, "Bản chép")
    make_chapter(client, b, sb["id"], content="\n".join(OWN + ORIGINAL[1:4]))

    reports = client.get("/api/plagiarism/reports", headers=admin).json()
    assert len(reports) == 1
    rep = reports[0]
    assert rep["suspect"]["author_username"] == "daovan" and rep["matched_count"] == 3
    assert client.get("/api/plagiarism/reports", headers=a).json()[0]["my_role"] == "source"

    kinds = lambda h: [n["kind"] for n in client.get("/api/notifications", headers=h).json()]
    assert "plagiarism_source" in kinds(a) and "plagiarism_suspect" in kinds(b)

    assert client.patch(f"/api/plagiarism/reports/{rep['id']}", json={"status": "confirmed"}, headers=a).status_code == 403
    assert client.patch(f"/api/plagiarism/reports/{rep['id']}", json={"status": "dismissed"}, headers=admin).json()["status"] == "dismissed"
    assert client.post("/api/plagiarism/reindex", headers=admin).json() == {"chapters": 2, "reports": 1}
