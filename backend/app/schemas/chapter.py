from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=100_000)
    is_published: bool = False


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=100_000)
    is_published: bool | None = None


class ChapterBrief(BaseModel):
    """Dùng cho mục lục — KHÔNG có nội dung."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    word_count: int
    is_published: bool
    created_at: datetime
    updated_at: datetime


class ChapterOut(ChapterBrief):
    """Dùng cho tác giả khi soạn/sửa — có nội dung."""
    story_id: int
    content: str
