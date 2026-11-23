from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_read_token
from app.models import User
from app.schemas.chapter import ChapterBrief
from app.schemas.reading import ReadSessionOut
from app.services.reading_service import (
    count_paragraphs,
    get_neighbor_ids,
    get_readable_chapter,
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