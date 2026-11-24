from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.models import Story, User
from app.schemas.story import (
    GenreOut,
    StoryCreate,
    StoryDetailOut,
    StoryOut,
    StorySort,
    StoryStatus,
    StoryUpdate,
)
from app.services.story_service import (
    create_story,
    delete_story,
    get_story,
    list_author_stories,
    list_genres,
    list_published_stories,
    update_story,
    viewer_state,
)

router = APIRouter(prefix="/api/stories", tags=["stories"])
genre_router = APIRouter(prefix="/api/genres", tags=["stories"])


@genre_router.get("", response_model=list[GenreOut])
def genres(db: Session = Depends(get_db)):
    return list_genres(db)


def get_owned_story(
    story_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Story:
    """Lấy truyện và kiểm tra người gọi có phải tác giả không."""
    story = get_story(db, story_id)
    if story is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy truyện")
    if story.author_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không phải tác giả của truyện này")
    return story


def get_public_story(story_id: int, db: Session = Depends(get_db)) -> Story:
    """Truyện đã xuất bản (dùng cho các trang công khai)."""
    story = get_story(db, story_id)
    if story is None or not story.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy truyện")
    return story


@router.get("", response_model=list[StoryOut])
def list_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    q: str | None = Query(None, max_length=100, description="Tìm theo tên truyện, giới thiệu, tác giả"),
    genre: str | None = Query(None, description="slug thể loại"),
    status_filter: StoryStatus | None = Query(None, alias="status"),
    sort: StorySort = "updated",
    db: Session = Depends(get_db),
):
    return list_published_stories(db, skip, limit, q, genre, status_filter, sort)


@router.get("/mine", response_model=list[StoryOut])
def my_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_author_stories(db, current_user.id)


@router.get("/{story_id}", response_model=StoryDetailOut)
def read_story(
    story: Story = Depends(get_public_story),
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    return StoryDetailOut.model_validate(
        {**StoryOut.model_validate(story).model_dump(), **viewer_state(db, story, viewer)}
    )


@router.post("", response_model=StoryOut, status_code=status.HTTP_201_CREATED)
def create(
    data: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return create_story(db, current_user, data)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.patch("/{story_id}", response_model=StoryOut)
def update(data: StoryUpdate, story: Story = Depends(get_owned_story), db: Session = Depends(get_db)):
    try:
        return update_story(db, story, data)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(story: Story = Depends(get_owned_story), db: Session = Depends(get_db)):
    delete_story(db, story)
