from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.embedder import EMBEDDING_DIM


class ParagraphEmbedding(Base):
    """Vector ngữ nghĩa của từng đoạn văn đủ dài (dùng để bắt văn bản viết lại)."""
    __tablename__ = "paragraph_embeddings"
    __table_args__ = (
        # Chỉ mục HNSW của pgvector: tìm vector gần nhất theo khoảng cách cosine mà không quét cả bảng
        Index(
            "ix_paragraph_embeddings_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # BigInteger trên PostgreSQL; Integer trên SQLite (chỉ để chạy test)
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    paragraph_index: Mapped[int] = mapped_column()
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM))
