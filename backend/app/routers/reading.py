from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_read_token, decode_read_token
from app.models import User
from app.schemas.chapter import ChapterBrief
from app.schemas.reading import ParagraphBatchOut, ParagraphOut, ReadSessionOut
from app.services.reading_service import (
    count_paragraphs,
    get_neighbor_ids,
    get_readable_chapter,
    split_paragraphs,
    start_reading_session,
)

router = APIRouter(
    prefix="/api/stories/{story_id}/chapters/{chapter_id}", tags=["reading"]
)


@router.post("/session", response_model=ReadSessionOut, status_code=status.HTTP_201_CREATED)
def open_reading_session(
    story_id: int,
    chapter_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chapter = get_readable_chapter(db, story_id, chapter_id)
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chương")

    ip = request.client.host if request.client else None
    user_agent = (request.headers.get("user-agent") or "")[:255]
    session = start_reading_session(db, current_user, chapter, ip, user_agent)
    prev_id, next_id = get_neighbor_ids(db, chapter)

    return ReadSessionOut(
        session_token=create_read_token(session.id, current_user.id, chapter.id),
        expires_in=settings.READ_TOKEN_EXPIRE_MINUTES * 60,
        story_id=chapter.story_id,
        story_title=chapter.story.title,
        chapter=ChapterBrief.model_validate(chapter),
        total_paragraphs=count_paragraphs(chapter.content),
        prev_chapter_id=prev_id,
        next_chapter_id=next_id,
    )


@router.get("/paragraphs", response_model=ParagraphBatchOut)
def read_paragraphs(
    story_id: int,
    chapter_id: int,
    start: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=settings.MAX_PARAGRAPHS_PER_REQUEST),
    x_read_token: str = Header(description="Vé đọc nhận từ POST .../session"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Vé đọc phải hợp lệ và còn hạn
    payload = decode_read_token(x_read_token)
    if payload is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Vé đọc không hợp lệ hoặc đã hết hạn"
        )

    # 2. Vé phải cấp cho đúng chương này và đúng người đang đăng nhập
    if payload.get("cid") != chapter_id or payload.get("sub") != str(current_user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vé đọc không dành cho yêu cầu này")

    # 3. Chương vẫn phải đang được xuất bản (tác giả có thể đã ẩn sau khi cấp vé)
    chapter = get_readable_chapter(db, story_id, chapter_id)
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chương")

    paragraphs = split_paragraphs(chapter.content)
    total = len(paragraphs)
    batch = paragraphs[start : start + limit]
    # TODO (phần sau): chèn watermark zero-width theo payload["sid"] vào từng đoạn

    return ParagraphBatchOut(
        chapter_id=chapter.id,
        start=start,
        total_paragraphs=total,
        has_more=start + len(batch) < total,
        paragraphs=[
            ParagraphOut(index=start + i, text=text) for i, text in enumerate(batch)
        ],
    )