"""So sánh ngữ nghĩa: tìm các đoạn ở chương khác có cùng ý dù viết bằng chữ khác."""
from collections import defaultdict

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.embedder import Embedder
from app.models import Chapter, ParagraphEmbedding

NEIGHBORS = 10  # số đoạn gần nhất lấy ra cho mỗi đoạn (có thể lẫn chương cũ của chính tác giả)


def split_paragraphs(content: str) -> list[str]:
    return content.split("\n\n") if content else []


def clear_embeddings(db: Session, chapter_id: int) -> None:
    db.execute(delete(ParagraphEmbedding).where(ParagraphEmbedding.chapter_id == chapter_id))


def index_embeddings(db: Session, chapter: Chapter, embedder: Embedder) -> dict[int, np.ndarray]:
    """Tính lại embedding cho các đoạn đủ dài của chương. Trả về {chỉ số đoạn: vector}."""
    clear_embeddings(db, chapter.id)
    picked = [
        (idx, text)
        for idx, text in enumerate(split_paragraphs(chapter.content))
        if len(text.split()) >= settings.SEMANTIC_MIN_WORDS
    ]
    if not picked:
        return {}
    vectors = embedder.embed([text for _, text in picked])
    result = {}
    for (idx, _), vec in zip(picked, vectors):
        db.add(ParagraphEmbedding(chapter_id=chapter.id, paragraph_index=idx, embedding=vec))
        result[idx] = vec
    db.flush()
    return result


def _neighbors_postgres(db: Session, chapter_id: int, vec: np.ndarray, k: int):
    distance = ParagraphEmbedding.embedding.cosine_distance(vec)
    stmt = (
        select(ParagraphEmbedding.chapter_id, ParagraphEmbedding.paragraph_index, distance.label("d"))
        .where(ParagraphEmbedding.chapter_id != chapter_id)
        .order_by(distance)
        .limit(k)
    )
    return [(cid, idx, 1.0 - float(d)) for cid, idx, d in db.execute(stmt)]


def _all_others(db: Session, chapter_id: int):
    rows = db.execute(
        select(ParagraphEmbedding.chapter_id, ParagraphEmbedding.paragraph_index, ParagraphEmbedding.embedding)
        .where(ParagraphEmbedding.chapter_id != chapter_id)
    ).all()
    if not rows:
        return [], np.zeros((0, 1))
    keys = [(r[0], r[1]) for r in rows]
    matrix = np.array([np.asarray(r[2], dtype=np.float32) for r in rows])
    return keys, matrix


def find_semantic_matches(
    db: Session, chapter: Chapter, vectors: dict[int, np.ndarray], threshold: float | None = None
) -> dict[int, list[tuple[int, int, float]]]:
    """{đoạn của mình: [(id chương khác, đoạn của họ, cosine)]} với cosine >= ngưỡng."""
    threshold = settings.SEMANTIC_THRESHOLD if threshold is None else threshold
    found: dict[int, list[tuple[int, int, float]]] = defaultdict(list)
    if not vectors:
        return found

    if db.get_bind().dialect.name == "postgresql":
        # PostgreSQL + pgvector: mỗi đoạn 1 truy vấn, dùng chỉ mục HNSW
        for idx, vec in vectors.items():
            for cid, other_idx, sim in _neighbors_postgres(db, chapter.id, vec, NEIGHBORS):
                if sim >= threshold:
                    found[idx].append((cid, other_idx, sim))
    else:
        # SQLite (môi trường test): tính bằng numpy trên toàn bộ vector
        keys, matrix = _all_others(db, chapter.id)
        if keys:
            for idx, vec in vectors.items():
                sims = matrix @ vec  # vector đã chuẩn hoá -> tích vô hướng = cosine
                for j in np.argsort(-sims)[:NEIGHBORS]:
                    if sims[j] >= threshold:
                        found[idx].append((keys[j][0], keys[j][1], float(sims[j])))
    return found
