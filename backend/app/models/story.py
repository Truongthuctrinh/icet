from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.genre import Genre, story_genres
if TYPE_CHECKING:
    from app.models.chapter import Chapter
    from app.models.user import User


class Story(Base):
    __tablename__ = "stories"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="ongoing")
    is_published: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Số liệu tổng hợp, cập nhật khi có đánh giá / theo dõi (để danh sách truyện không phải đếm lại)
    rating_avg: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    rating_count: Mapped[int] = mapped_column(default=0, server_default="0")
    follower_count: Mapped[int] = mapped_column(default=0, server_default="0")

    author: Mapped["User"] = relationship(back_populates="stories")
    genres: Mapped[list[Genre]] = relationship(secondary=story_genres, order_by=Genre.name)
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="story", cascade="all, delete-orphan", order_by="Chapter.number")
