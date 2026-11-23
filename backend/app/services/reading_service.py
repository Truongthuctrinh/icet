from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Chapter, ReadingSession, Story, User


def get_readable_chapter(db: Session, story_id: int, chapter_id: int) -> Chapter | None:
    """Chỉ trả về chương đã xuất bản thuộc truyện đã xuất bản."""
    stmt = (
        select(Chapter)
        .join(Chapter.story)
        .where(
            Chapter.id == chapter_id,
            Chapter.story_id == story_id,
            Chapter.is_published.is_(True),
            Story.is_published.is_(True),
        )
        .options(selectinload(Chapter.story))
    )
    return db.scalar(stmt)


def count_paragraphs(content: str) -> int:
    return content.count("\n\n") + 1 if content else 0


def get_neighbor_ids(db: Session, chapter: Chapter) -> tuple[int | None, int | None]:
    """id chương trước / sau (chỉ tính chương đã xuất bản)."""
    base = select(Chapter.id).where(
        Chapter.story_id == chapter.story_id, Chapter.is_published.is_(True)
    )
    prev_id = db.scalar(
        base.where(Chapter.number < chapter.number).order_by(Chapter.number.desc()).limit(1)
    )
    next_id = db.scalar(
        base.where(Chapter.number > chapter.number).order_by(Chapter.number.asc()).limit(1)
    )
    return prev_id, next_id


def start_reading_session(
    db: Session, user: User, chapter: Chapter, ip: str | None, user_agent: str | None
) -> ReadingSession:
    session = ReadingSession(
        user_id=user.id, chapter_id=chapter.id, ip_address=ip, user_agent=user_agent
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session