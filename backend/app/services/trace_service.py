from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.watermark import extract_session_ids
from app.models import Chapter, ReadingSession, Story, User
from app.schemas.trace import TraceMatch, TraceResult


def trace_text(db: Session, text: str, requester: User) -> TraceResult:
    marks_found, session_ids = extract_session_ids(text)
    if not session_ids:
        return TraceResult(marks_found=marks_found, sessions_found=0, hidden_matches=0, matches=[])

    stmt = (
        select(ReadingSession, User, Chapter, Story)
        .join(User, ReadingSession.user_id == User.id)
        .join(Chapter, ReadingSession.chapter_id == Chapter.id)
        .join(Story, Chapter.story_id == Story.id)
        .where(ReadingSession.id.in_(session_ids))
        .order_by(ReadingSession.created_at.desc())
    )

    matches: list[TraceMatch] = []
    hidden = 0
    for session, reader, chapter, story in db.execute(stmt).all():
        # Tác giả chỉ truy vết được truyện của chính mình; admin xem được tất cả
        if requester.role != "admin" and story.author_id != requester.id:
            hidden += 1
            continue
        matches.append(
            TraceMatch(
                session_id=session.id,
                read_at=session.created_at,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                reader_username=reader.username,
                reader_display_name=reader.display_name,
                story_id=story.id,
                story_title=story.title,
                chapter_id=chapter.id,
                chapter_number=chapter.number,
                chapter_title=chapter.title,
            )
        )

    return TraceResult(
        marks_found=marks_found,
        sessions_found=len(session_ids),
        hidden_matches=hidden,
        matches=matches,
    )
