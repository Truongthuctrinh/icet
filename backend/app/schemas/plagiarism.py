from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ReportStatus = Literal["pending", "confirmed", "dismissed"]


class ChapterRef(BaseModel):
    chapter_id: int
    chapter_number: int
    chapter_title: str
    story_id: int
    story_title: str
    author_username: str
    author_display_name: str
    created_at: datetime


class MatchedParagraph(BaseModel):
    suspect_index: int
    source_index: int
    similarity: float
    method: Literal["minhash", "semantic"] = "minhash"  # trùng nguyên văn / trùng ý (viết lại)
    suspect_text: str
    source_text: str


class ReportOut(BaseModel):
    id: int
    score: float  # 0..1: tỉ lệ chữ của chương nghi đạo bị trùng
    matched_count: int
    status: ReportStatus
    my_role: Literal["admin", "source", "suspect"]  # người xem là admin / tác giả bản gốc / tác giả bị nghi
    suspect: ChapterRef
    source: ChapterRef
    matches: list[MatchedParagraph]
    watermark_sessions: list[int]
    created_at: datetime
    updated_at: datetime


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class ReindexResult(BaseModel):
    chapters: int
    reports: int  # -1 khi đã giao cho worker (chưa có kết quả)
    queued: bool = False
