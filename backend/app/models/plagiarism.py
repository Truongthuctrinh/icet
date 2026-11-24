from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ParagraphLSH(Base):
    """Chỉ mục LSH: mỗi đoạn văn đủ dài có 32 dòng (1 dòng / 1 dải của chữ ký MinHash)."""
    __tablename__ = "paragraph_lsh"
    __table_args__ = (Index("ix_paragraph_lsh_band_bucket", "band", "bucket"),)

    # BigInteger trên PostgreSQL; Integer trên SQLite (chỉ để chạy test)
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), index=True
    )
    paragraph_index: Mapped[int] = mapped_column()
    band: Mapped[int] = mapped_column(SmallInteger)
    bucket: Mapped[int] = mapped_column(BigInteger)


class PlagiarismReport(Base):
    """Cảnh báo: chương `suspect` (đăng sau) trùng nội dung với chương `source` (đăng trước)."""
    __tablename__ = "plagiarism_reports"
    __table_args__ = (
        UniqueConstraint("suspect_chapter_id", "source_chapter_id", name="uq_report_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    suspect_chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), index=True
    )
    source_chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[float] = mapped_column(Float)  # tỉ lệ chữ của chương suspect bị trùng (0..1)
    matched_count: Mapped[int] = mapped_column()  # số đoạn trùng
    matches: Mapped[list] = mapped_column(JSON, default=list)  # [{suspect_index, source_index, similarity}]
    watermark_sessions: Mapped[list] = mapped_column(JSON, default=list)  # id phiên đọc tìm thấy trong chương suspect
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | confirmed | dismissed
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    suspect_chapter: Mapped["Chapter"] = relationship(foreign_keys=[suspect_chapter_id])  # noqa: F821
    source_chapter: Mapped["Chapter"] = relationship(foreign_keys=[source_chapter_id])  # noqa: F821
