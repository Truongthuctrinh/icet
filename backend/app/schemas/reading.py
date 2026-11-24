from pydantic import BaseModel

from app.schemas.chapter import ChapterBrief


class ReadSessionOut(BaseModel):
    session_token: str
    expires_in: int  # giây
    story_id: int
    story_title: str
    story_author_id: int  # để giao diện biết ai được kiểm duyệt bình luận
    chapter: ChapterBrief  # không có nội dung
    total_paragraphs: int
    prev_chapter_id: int | None
    next_chapter_id: int | None


class ParagraphOut(BaseModel):
    index: int  # vị trí đoạn trong chương, bắt đầu từ 0
    text: str


class ParagraphBatchOut(BaseModel):
    chapter_id: int
    start: int
    total_paragraphs: int
    has_more: bool
    paragraphs: list[ParagraphOut]
