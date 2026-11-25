"""Biến đoạn văn thành vector ngữ nghĩa (embedding).

Model mặc định: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  - đa ngôn ngữ (có tiếng Việt), 384 chiều, ~0,22 GB, chạy bằng CPU qua ONNX (thư viện fastembed)
  - được huấn luyện để 2 câu cùng ý (dù khác chữ) có vector gần nhau -> bắt được văn bản viết lại
Chỉ worker nạp model (tốn RAM vài trăm MB); API không nạp.
"""
import logging
import unicodedata
from typing import Protocol

import numpy as np

from app.core.config import settings
from app.core.watermark import strip_marks

logger = logging.getLogger("icet.embedder")

EMBEDDING_DIM = 384


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> np.ndarray:
        """Trả về ma trận (số đoạn, EMBEDDING_DIM), mỗi dòng đã chuẩn hoá độ dài = 1."""
        ...


def prepare(text: str) -> str:
    """Bỏ watermark + chuẩn hoá Unicode trước khi đưa vào model."""
    return unicodedata.normalize("NFC", strip_marks(text)).strip()


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class FastEmbedEmbedder:
    def __init__(self, model_name: str, cache_dir: str | None = None):
        from fastembed import TextEmbedding  # import muộn: API không cần thư viện này

        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir or None)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        vectors = np.array(list(self.model.embed([prepare(t) for t in texts])), dtype=np.float32)
        return normalize_rows(vectors)


def load_embedder() -> Embedder | None:
    """Nạp model 1 lần khi worker khởi động. Lỗi (chưa cài, chưa tải được model) -> None:
    hệ thống vẫn chạy, chỉ bỏ qua bước so sánh ngữ nghĩa."""
    if not settings.EMBEDDING_ENABLED:
        return None
    try:
        embedder = FastEmbedEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_CACHE_DIR)
        embedder.embed(["khởi động model"])  # chạy thử 1 lần để lỗi lộ ra ngay lúc khởi động
        logger.info("Đã nạp model embedding %s", settings.EMBEDDING_MODEL)
        return embedder
    except Exception:
        logger.exception("Không nạp được model embedding, bỏ qua so sánh ngữ nghĩa")
        return None
