from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.story import Story


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("story_id", "number", name="uq_chapter_story_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(
        ForeignKey("stories.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column()  # chương số mấy
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)  # văn bản thuần, đoạn cách nhau bằng dòng trống
    word_count: Mapped[int] = mapped_column(default=0)
    is_published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    story: Mapped["Story"] = relationship(back_populates="chapters")