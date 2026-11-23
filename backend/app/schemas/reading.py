from pydantic import BaseModel

from app.schemas.chapter import ChapterBrief


class ReadSessionOut(BaseModel):
    session_token: str
    expires_in: int  # giây
    story_id: int
    story_title: str
    chapter: ChapterBrief  # không có nội dung
    total_paragraphs: int
    prev_chapter_id: int | None
    next_chapter_id: int | None