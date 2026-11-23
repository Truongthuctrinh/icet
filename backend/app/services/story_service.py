from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Story, User
from app.schemas.story import StoryCreate, StoryUpdate


def create_story(db: Session, author: User, data: StoryCreate) -> Story:
    story = Story(author_id=author.id, **data.model_dump())
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


def list_published_stories(db: Session, skip: int, limit: int) -> list[Story]:
    stmt = (
        select(Story)
        .where(Story.is_published.is_(True))
        .options(selectinload(Story.author))  # tải tác giả 1 lần, tránh N+1
        .order_by(Story.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt))


def list_author_stories(db: Session, author_id: int) -> list[Story]:
    stmt = (
        select(Story)
        .where(Story.author_id == author_id)
        .options(selectinload(Story.author))
        .order_by(Story.updated_at.desc())
    )
    return list(db.scalars(stmt))


def get_story(db: Session, story_id: int) -> Story | None:
    stmt = select(Story).where(Story.id == story_id).options(selectinload(Story.author))
    return db.scalar(stmt)


def update_story(db: Session, story: Story, data: StoryUpdate) -> Story:
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(story, field, value)
    db.commit()
    db.refresh(story)
    return story


def delete_story(db: Session, story: Story) -> None:
    db.delete(story)
    db.commit()