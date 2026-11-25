"""Đo độ giống (cosine) của model embedding trên vài cặp đoạn tiếng Việt để chọn SEMANTIC_THRESHOLD.

Chạy (đã activate venv, đứng ở thư mục backend):
    python -m app.scripts.calibrate_embedding
Lần đầu sẽ tải model (~220 MB).

Cách đọc kết quả: chọn ngưỡng NẰM GIỮA điểm thấp nhất của nhóm "viết lại" và điểm cao nhất
của nhóm "cùng chủ đề". Rồi ghi vào file .env:  SEMANTIC_THRESHOLD=0.xx
Có thể thêm cặp câu của chính bạn vào danh sách PAIRS bên dưới để đo kỹ hơn.
"""
from app.core.config import settings
from app.core.embedder import FastEmbedEmbedder

ORIGINAL = (
    "Người lái đò bảo cô đừng lặn vào buổi chiều. Ông nói khi mặt trời chếch về phía núi, "
    "nước hồ đổi màu, và những ai ở dưới đó bắt đầu thức dậy."
)
ORIGINAL_2 = (
    "Lam cười, buộc lại dây kính lặn. Cô không tin chuyện ma quỷ. Cô chỉ muốn tìm lại chiếc hộp "
    "thiếc mẹ đã chôn dưới gốc cây khế trước nhà."
)

PAIRS = [
    ("chép nguyên văn", ORIGINAL, ORIGINAL),
    ("chép, sửa vài chữ", ORIGINAL,
     "Người lái đò dặn cô đừng lặn vào lúc chiều. Ông bảo khi mặt trời chếch về phía núi, "
     "nước hồ đổi màu, và những kẻ ở dưới đó bắt đầu thức dậy."),
    ("viết lại", ORIGINAL,
     "Ông chèo thuyền dặn nàng chớ có xuống nước lúc hoàng hôn. Theo ông, lúc nắng nghiêng về "
     "phía đồi, hồ chuyển sắc và những kẻ dưới ấy tỉnh dậy."),
    ("viết lại", ORIGINAL_2,
     "Lam mỉm cười, thắt lại kính lặn. Nàng chẳng tin ma quỷ gì cả. Nàng chỉ mong tìm được cái "
     "rương thiếc má từng vùi dưới gốc khế trước nhà."),
    ("viết lại + đảo câu", ORIGINAL_2,
     "Dưới gốc khế trước nhà có chiếc hộp thiếc mẹ chôn năm nào, và Lam chỉ muốn tìm lại nó. "
     "Ma quỷ ư? Cô chẳng tin. Cô cười rồi chỉnh lại dây kính."),
    ("cùng chủ đề, khác nội dung", ORIGINAL,
     "Bà cụ bán nước đầu bến kể rằng hồ này sâu lắm, năm nào cũng có người chết đuối, "
     "nên dân làng thường thắp hương bên bờ vào ngày rằm."),
    ("cùng chủ đề, khác nội dung", ORIGINAL_2,
     "Mẹ Lam mất năm cô mười hai tuổi. Cô chỉ còn giữ chiếc khăn len màu xám và vài tấm ảnh "
     "chụp cả nhà trước hiên, bên cạnh cây khế đang ra hoa."),
    ("không liên quan", ORIGINAL,
     "Chợ phiên sáng chủ nhật đông nghịt người, tiếng rao hàng lẫn tiếng gà vịt inh ỏi khắp "
     "con dốc dẫn lên đình làng."),
    ("không liên quan", ORIGINAL_2,
     "Thằng Tí chạy ù ra đồng thả diều, sợi dây gai căng phần phật trong gió nồm, con diều "
     "sáo kêu vi vu suốt buổi trưa."),
]


def main() -> None:
    print(f"Model: {settings.EMBEDDING_MODEL}")
    print(f"Ngưỡng hiện tại: SEMANTIC_THRESHOLD = {settings.SEMANTIC_THRESHOLD}\n")
    embedder = FastEmbedEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_CACHE_DIR)
    by_kind: dict[str, list[float]] = {}
    for kind, a, b in PAIRS:
        va, vb = embedder.embed([a, b])
        score = float(va @ vb)
        by_kind.setdefault(kind, []).append(score)
        flag = "TRÙNG" if score >= settings.SEMANTIC_THRESHOLD else "-"
        print(f"{score:.3f}  {flag:5}  {kind}")

    rewrites = by_kind["viết lại"] + by_kind["viết lại + đảo câu"]
    same_topic = by_kind["cùng chủ đề, khác nội dung"] + by_kind["không liên quan"]
    low, high = min(rewrites), max(same_topic)
    print(f"\nViết lại thấp nhất: {low:.3f} | Không phải chép cao nhất: {high:.3f}")
    if low > high:
        print(f"Gợi ý: SEMANTIC_THRESHOLD = {round((low + high) / 2, 2)}")
    else:
        print("Hai nhóm chồng lên nhau: nên đặt ngưỡng gần mức 'viết lại thấp nhất' để tránh báo nhầm,"
              " chấp nhận bỏ sót vài đoạn viết lại quá khác.")


if __name__ == "__main__":
    main()
