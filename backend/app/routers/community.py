from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limit_by_user
from app.models import Chapter, Story, User
from app.routers.stories import get_public_story
from app.schemas.community import (
    CommentCreate,
    CommentOut,
    CommentUpdate,
    FollowState,
    NotificationOut,
    ProfileOut,
    RatingOut,
    RatingSummary,
    RatingUpsert,
    UnreadCount,
)
from app.schemas.story import StoryOut
from app.services import community_service as cs
from app.services import notification_service as ns
from app.services.reading_service import get_readable_chapter
from app.services.story_service import list_author_stories

router = APIRouter(tags=["community"])


# ---------- Bình luận theo chương ----------

def get_readable(story_id: int, chapter_id: int, db: Session = Depends(get_db)) -> Chapter:
    chapter = get_readable_chapter(db, story_id, chapter_id)
    if chapter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chương")
    return chapter


COMMENTS = "/api/stories/{story_id}/chapters/{chapter_id}/comments"


@router.get(COMMENTS, response_model=list[CommentOut])
def list_comments(chapter: Chapter = Depends(get_readable), db: Session = Depends(get_db)):
    return cs.list_comments(db, chapter)


@router.post(
    COMMENTS,
    status_code=status.HTTP_201_CREATED,
    response_model=list[CommentOut],
    dependencies=[Depends(limit_by_user("comment", settings.RATE_COMMENT_PER_MIN, 60))],
)
def add_comment(
    data: CommentCreate,
    chapter: Chapter = Depends(get_readable),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trả về toàn bộ danh sách bình luận mới để giao diện cập nhật 1 lần."""
    try:
        cs.create_comment(db, chapter, current_user, data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return cs.list_comments(db, chapter)


@router.patch(COMMENTS + "/{comment_id}", response_model=list[CommentOut])
def edit_comment(
    comment_id: int,
    data: CommentUpdate,
    chapter: Chapter = Depends(get_readable),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = cs.get_comment(db, chapter, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bình luận")
    if comment.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn chỉ sửa được bình luận của mình")
    cs.update_comment(db, comment, data.content)
    return cs.list_comments(db, chapter)


@router.delete(COMMENTS + "/{comment_id}", response_model=list[CommentOut])
def remove_comment(
    comment_id: int,
    chapter: Chapter = Depends(get_readable),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Người viết, tác giả truyện (kiểm duyệt) hoặc admin được xoá."""
    comment = cs.get_comment(db, chapter, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bình luận")
    allowed = {comment.user_id, chapter.story.author_id}
    if current_user.id not in allowed and current_user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bạn không có quyền xoá bình luận này")
    cs.delete_comment(db, comment)
    return cs.list_comments(db, chapter)


# ---------- Đánh giá truyện ----------

@router.get("/api/stories/{story_id}/ratings", response_model=RatingSummary)
def ratings(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    story: Story = Depends(get_public_story),
    db: Session = Depends(get_db),
):
    return cs.rating_summary(db, story, skip, limit)


@router.put("/api/stories/{story_id}/ratings/me", response_model=RatingOut)
def rate(
    data: RatingUpsert,
    story: Story = Depends(get_public_story),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return cs.upsert_rating(db, story, current_user, data)
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


@router.delete("/api/stories/{story_id}/ratings/me", status_code=status.HTTP_204_NO_CONTENT)
def unrate(
    story: Story = Depends(get_public_story),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cs.delete_rating(db, story, current_user)


# ---------- Theo dõi truyện ----------

@router.post("/api/stories/{story_id}/follow", response_model=FollowState)
def follow(
    story: Story = Depends(get_public_story),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cs.follow_story(db, story, current_user)
    return FollowState(is_following=True, follower_count=story.follower_count)


@router.delete("/api/stories/{story_id}/follow", response_model=FollowState)
def unfollow(
    story: Story = Depends(get_public_story),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cs.unfollow_story(db, story, current_user)
    return FollowState(is_following=False, follower_count=story.follower_count)


@router.get("/api/me/following", response_model=list[StoryOut])
def my_following(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cs.followed_stories(db, current_user)


# ---------- Thông báo ----------

@router.get("/api/notifications", response_model=list[NotificationOut])
def notifications(
    unread_only: bool = False,
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ns.list_notifications(db, current_user.id, unread_only, limit)


@router.get("/api/notifications/unread-count", response_model=UnreadCount)
def notifications_unread(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return UnreadCount(count=ns.unread_count(db, current_user.id))


@router.post("/api/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not ns.mark_read(db, current_user.id, notification_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thông báo")


@router.post("/api/notifications/read-all", response_model=UnreadCount)
def read_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ns.mark_all_read(db, current_user.id)
    return UnreadCount(count=0)


# ---------- Hồ sơ tác giả ----------

@router.get("/api/users/{username}", response_model=ProfileOut)
def profile(username: str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == username, User.is_active.is_(True)))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người dùng")
    stories = list_author_stories(db, user.id, only_published=True)
    return ProfileOut(
        username=user.username,
        display_name=user.display_name,
        created_at=user.created_at,
        story_count=len(stories),
        total_followers=sum(s.follower_count for s in stories),
        stories=stories,
    )
