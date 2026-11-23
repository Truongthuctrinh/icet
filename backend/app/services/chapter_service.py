import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session, defer

from app.models import Chapter, Story
from app.schemas.chapter import ChapterCreate, ChapterUpdate


def normalize_content(text: str) -> str:
    """Chuẩn hoá: Unicode NFC, mỗi dòng không rỗng là 1 đoạn, các đoạn cách nhau 1 dòng trống."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n\n".join(paragraphs)


def count_words(text: str) -> int:
    return len(text.split())


def create_chapter(db: Session, story: Story, data: ChapterCreate) -> Chapter:
    content = normalize_content(data.content)
    if not content:
        raise ValueError("Nội dung chương không được để trống")

    last_number = db.scalar(
        select(func.max(Chapter.number)).where(Chapter.story_id == story.id)
    )
    chapter = Chapter(
        story_id=story.id,
        number=(last_number or 0) + 1,
        title=data.title,
        content=content,
        word_count=count_words(content),
        is_published=data.is_published,
    )
    db.add(chapter)
    if chapter.is_published:
        story.updated_at = func.now()  # đẩy truyện lên "mới cập nhật"
    db.commit()
    db.refresh(chapter)
    return chapter


def list_chapters(db: Session, story_id: int, only_published: bool) -> list[Chapter]:
    stmt = (
        select(Chapter)
        .where(Chapter.story_id == story_id)
        .options(defer(Chapter.content))  # mục lục không cần nội dung → không tải
        .order_by(Chapter.number)
    )
    if only_published:
        stmt = stmt.where(Chapter.is_published.is_(True))
    return list(db.scalars(stmt))


def get_chapter(db: Session, story_id: int, chapter_id: int) -> Chapter | None:
    stmt = select(Chapter).where(
        Chapter.id == chapter_id, Chapter.story_id == story_id
    )
    return db.scalar(stmt)


def update_chapter(db: Session, chapter: Chapter, data: ChapterUpdate) -> Chapter:
    values = data.model_dump(exclude_unset=True, exclude_none=True)
    if "content" in values:
        content = normalize_content(values["content"])
        if not content:
            raise ValueError("Nội dung chương không được để trống")
        values["content"] = content
        values["word_count"] = count_words(content)

    for field, value in values.items():
        setattr(chapter, field, value)
    if chapter.is_published:
        chapter.story.updated_at = func.now()
    db.commit()
    db.refresh(chapter)
    return chapter


def delete_chapter(db: Session, chapter: Chapter) -> None:
    db.delete(chapter)
    db.commit()