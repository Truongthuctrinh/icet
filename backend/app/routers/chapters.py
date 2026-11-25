from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Chapter, Story
from app.routers.stories import get_owned_story
from app.schemas.chapter import ChapterBrief, ChapterCreate, ChapterOut, ChapterUpdate
from app.services.chapter_service import (
    create_chapter,
    delete_chapter,
    get_chapter,
    list_chapters,
    update_chapter,
)
from app.core.task_queue import schedule_plagiarism_check
from app.services.plagiarism_service import locked_chapter_ids
from app.services.story_service import get_story

router = APIRouter(prefix="/api/stories/{story_id}/chapters", tags=["chapters"])


def get_owned_chapter(
    chapter_id: int,
    story: Story = Depends(get_owned_story),
    db: Session = Depends(get_db),
) -> Chapter:
    """Lấy chương, đồng thời kiểm tra người gọi là tác giả của truyện."""
    chapter = get_chapter(db, story.id, chapter_id)
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chương")
    return chapter


@router.get("", response_model=list[ChapterBrief])
def table_of_contents(story_id: int, db: Session = Depends(get_db)):
    """Mục lục công khai: chỉ chương đã xuất bản của truyện đã xuất bản."""
    story = get_story(db, story_id)
    if story is None or not story.is_published:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy truyện")
    return list_chapters(db, story_id, only_published=True)


@router.get("/manage", response_model=list[ChapterBrief])
def manage_chapters(
    story: Story = Depends(get_owned_story), db: Session = Depends(get_db)
):
    """Góc tác giả: tất cả chương, kể cả bản nháp; đánh dấu chương bị khoá do đạo văn."""
    chapters = list_chapters(db, story.id, only_published=False)
    locked = locked_chapter_ids(db, [c.id for c in chapters])
    return [ChapterBrief.model_validate(c).model_copy(update={"is_locked": c.id in locked}) for c in chapters]


@router.post("", response_model=ChapterOut, status_code=status.HTTP_201_CREATED)
def create(
    data: ChapterCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    story: Story = Depends(get_owned_story),
    db: Session = Depends(get_db),
):
    try:
        chapter = create_chapter(db, story, data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    # Kiểm tra đạo văn: đưa sang worker (hoặc chạy nền sau khi trả kết quả) -> tác giả không phải chờ
    background_tasks.add_task(schedule_plagiarism_check, request.app, chapter.id)
    return chapter


@router.get("/{chapter_id}/edit", response_model=ChapterOut)
def read_for_edit(chapter: Chapter = Depends(get_owned_chapter)):
    return chapter


@router.patch("/{chapter_id}", response_model=ChapterOut)
def update(
    data: ChapterUpdate,
    request: Request,
    background_tasks: BackgroundTasks,
    chapter: Chapter = Depends(get_owned_chapter),
    db: Session = Depends(get_db),
):
    try:
        updated = update_chapter(db, chapter, data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if data.content is not None:  # chỉ kiểm tra lại khi nội dung thay đổi
        background_tasks.add_task(schedule_plagiarism_check, request.app, updated.id)
    return updated


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(chapter: Chapter = Depends(get_owned_chapter), db: Session = Depends(get_db)):
    delete_chapter(db, chapter)
