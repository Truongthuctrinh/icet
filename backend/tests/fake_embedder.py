"""Embedder giả cho test (không cần tải model): túi từ + bảng từ đồng nghĩa.

Hai đoạn dùng từ đồng nghĩa / đảo thứ tự câu vẫn cho cosine cao, giống cách model thật
nhận ra văn bản viết lại. Chỉ dùng để kiểm tra LUỒNG XỬ LÝ, không đo độ chính xác.
"""
import re
import zlib

import numpy as np

from app.core.embedder import EMBEDDING_DIM, normalize_rows, prepare

SYNONYMS = {
    "trở": "quay", "về": "về", "lại": "về",
    "thị": "phố", "trấn": "phố", "phố": "phố", "huyện": "phố",
    "hồ": "hồ", "nước": "nước",
    "lũ": "lũ", "lụt": "lũ",
    "phẳng": "lặng", "lặng": "lặng", "yên": "lặng", "êm": "lặng",
    "mây": "mây", "trôi": "trôi", "lướt": "trôi",
    "ngói": "mái", "mái": "mái",
    "trường": "trường", "học": "trường",
    "lái": "đò", "đò": "đò", "chèo": "đò", "thuyền": "đò",
    "dặn": "bảo", "bảo": "bảo", "nói": "bảo", "khuyên": "bảo",
    "lặn": "lặn", "xuống": "lặn",
    "chiều": "chiều", "hoàng": "chiều", "hôn": "chiều",
    "trời": "trời", "nắng": "trời",
    "núi": "núi", "đồi": "núi",
    "đổi": "đổi", "chuyển": "đổi", "biến": "đổi",
    "màu": "màu", "sắc": "màu",
    "thức": "thức", "dậy": "thức", "tỉnh": "thức",
    "cười": "cười", "mỉm": "cười",
    "kính": "kính", "buộc": "buộc", "thắt": "buộc",
    "tin": "tin", "ma": "ma", "quỷ": "ma",
    "hộp": "hộp", "thiếc": "hộp", "rương": "hộp",
    "mẹ": "mẹ", "má": "mẹ",
    "chôn": "chôn", "vùi": "chôn",
    "cây": "cây", "gốc": "cây", "khế": "cây",
    "nhà": "nhà",
    "lạnh": "lạnh", "buốt": "lạnh", "giá": "lạnh",
    "sâu": "sâu", "mét": "sâu",
    "ánh": "sáng", "sáng": "sáng",
    "mờ": "mờ", "nhạt": "mờ", "tối": "mờ",
    "xanh": "xanh", "ngọc": "xanh", "lục": "xanh",
    "tên": "tên",
    "chuông": "chuông", "hồi": "chuông", "tiếng": "chuông", "kêu": "chuông", "reo": "chuông",
    "lớp": "lớp", "hàng": "lớp", "xếp": "lớp",
    "cô": "lam", "lam": "lam", "nàng": "lam",
    "nhìn": "thấy", "chếch": "nghiêng", "muốn": "mong", "tưởng": "nghĩ", "chuyện": "ma",
}
STOPWORDS = {"và", "của", "thì", "là", "mà", "những", "các", "một", "đã", "đang", "sẽ", "rồi", "đến", "khi", "đó", "này", "có", "không", "ở",
             # hư từ / từ nối: model thật cũng gần như bỏ qua khi so nghĩa
             "mức", "nỗi", "thể", "được", "qua", "ngang", "từ", "kể", "mới", "tiên", "sau", "ai", "buổi",
             "bắt", "vào", "đầu", "đừng", "chớ", "kẻ", "lúc", "theo", "ấy", "người", "chiếc", "cái", "chẳng",
             "cả", "gì", "từng", "dần", "đi", "thứ", "độ", "chừng", "kế", "đặt", "mặt", "dây"}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"\w+", prepare(text).lower())
    return [SYNONYMS.get(w, w) for w in words if w not in STOPWORDS]


class FakeEmbedder:
    def embed(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in _tokens(text):
                matrix[row, zlib.crc32(token.encode()) % EMBEDDING_DIM] += 1.0
        return normalize_rows(matrix)
