from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Bảng nối nhiều-nhiều: 1 truyện có nhiều thể loại, 1 thể loại có nhiều truyện
story_genres = Table(
    "story_genres",
    Base.metadata,
    Column("story_id", ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(50))


# Danh sách thể loại mặc định, tự thêm khi khởi động nếu bảng còn trống
DEFAULT_GENRES = [
    ("ngon-tinh", "Ngôn tình"),
    ("tien-hiep", "Tiên hiệp"),
    ("huyen-huyen", "Huyền huyễn"),
    ("kinh-di", "Kinh dị"),
    ("trinh-tham", "Trinh thám"),
    ("khoa-hoc-vien-tuong", "Khoa học viễn tưởng"),
    ("hoc-duong", "Học đường"),
    ("doi-thuong", "Đời thường"),
    ("lich-su", "Lịch sử"),
    ("phieu-luu", "Phiêu lưu"),
    ("hai-huoc", "Hài hước"),
    ("tho-tan-van", "Thơ, tản văn"),
]
