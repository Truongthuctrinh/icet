from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Follow, Genre, Rating, Story, User
from app.schemas.story import StoryCreate, StoryUpdate

_LOAD = (selectinload(Story.author), selectinload(Story.genres))

SORTS = {
    "updated": (Story.updated_at.desc(),),
    "new": (Story.created_at.desc(),),
    "rating": (Story.rating_avg.desc(), Story.rating_count.desc()),
    "followers": (Story.follower_count.desc(), Story.updated_at.desc()),
}


def _genres_by_ids(db: Session, genre_ids: list[int]) -> list[Genre]:
    if not genre_ids:
        return []
    genres = list(db.scalars(select(Genre).where(Genre.id.in_(set(genre_ids)))))
    if len(genres) != len(set(genre_ids)):
        raise ValueError("Có thể loại không tồn tại")
    return genres


def create_story(db: Session, author: User, data: StoryCreate) -> Story:
    values = data.model_dump(exclude={"genre_ids"})
    story = Story(author_id=author.id, **values)
    story.genres = _genres_by_ids(db, data.genre_ids)
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


def list_published_stories(
    db: Session,
    skip: int,
    limit: int,
    q: str | None = None,
    genre: str | None = None,
    status: str | None = None,
    sort: str = "updated",
) -> list[Story]:
    stmt = select(Story).where(Story.is_published.is_(True)).options(*_LOAD)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.join(Story.author).where(
            or_(
                Story.title.ilike(pattern),
                Story.description.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )
    if genre:
        stmt = stmt.where(Story.genres.any(Genre.slug == genre))
    if status:
        stmt = stmt.where(Story.status == status)
    stmt = stmt.order_by(*SORTS.get(sort, SORTS["updated"])).offset(skip).limit(limit)
    return list(db.scalars(stmt))


def list_author_stories(db: Session, author_id: int, only_published: bool = False) -> list[Story]:
    stmt = select(Story).where(Story.author_id == author_id).options(*_LOAD)
    if only_published:
        stmt = stmt.where(Story.is_published.is_(True))
    return list(db.scalars(stmt.order_by(Story.updated_at.desc())))


def get_story(db: Session, story_id: int) -> Story | None:
    return db.scalar(select(Story).where(Story.id == story_id).options(*_LOAD))


def update_story(db: Session, story: Story, data: StoryUpdate) -> Story:
    values = data.model_dump(exclude_unset=True, exclude_none=True, exclude={"genre_ids"})
    for field, value in values.items():
        setattr(story, field, value)
    if data.genre_ids is not None:
        story.genres = _genres_by_ids(db, data.genre_ids)
    db.commit()
    db.refresh(story)
    return story


def delete_story(db: Session, story: Story) -> None:
    db.delete(story)
    db.commit()


def viewer_state(db: Session, story: Story, viewer: User | None) -> dict:
    """is_following + my_rating của người đang xem."""
    if viewer is None:
        return {"is_following": False, "my_rating": None}
    following = db.get(Follow, (viewer.id, story.id)) is not None
    rating = db.scalar(
        select(Rating).where(Rating.story_id == story.id, Rating.user_id == viewer.id)
    )
    return {"is_following": following, "my_rating": rating}


def list_genres(db: Session) -> list[Genre]:
    return list(db.scalars(select(Genre).order_by(Genre.name)))


def count_published(db: Session, author_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Story).where(
            Story.author_id == author_id, Story.is_published.is_(True)
        )
    )
