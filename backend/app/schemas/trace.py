from datetime import datetime

from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class TraceMatch(BaseModel):
    session_id: int
    read_at: datetime
    ip_address: str | None
    user_agent: str | None
    reader_username: str
    reader_display_name: str
    story_id: int
    story_title: str
    chapter_id: int
    chapter_number: int
    chapter_title: str


class TraceResult(BaseModel):
    marks_found: int  # số dấu ẩn tìm thấy trong văn bản
    sessions_found: int  # số phiên đọc khác nhau giải mã được
    hidden_matches: int  # phiên đọc thuộc truyện của tác giả khác -> không hiển thị
    matches: list[TraceMatch]
