from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Chapter, Comment, Follow, Rating, Story, User
from app.schemas.community import CommentCreate, RatingUpsert
from app.services.notification_service import notify


# ---------- Bình luận ----------

def list_comments(db: Session, chapter: Chapter) -> list[dict]:
    """Bình luận gốc (mới nhất trước) kèm các trả lời (cũ nhất trước)."""
    comments = list(
        db.scalars(
            select(Comment)
            .where(Comment.chapter_id == chapter.id)
            .options(selectinload(Comment.user))
            .order_by(Comment.created_at, Comment.id)
        )
    )
    author_id = chapter.story.author_id
    replies: dict[int, list[dict]] = defaultdict(list)
    roots: list[dict] = []
    for c in comments:
        item = {
            "id": c.id,
            "content": "" if c.is_deleted else c.content,
            "is_deleted": c.is_deleted,
            "is_edited": not c.is_deleted and c.updated_at is not None
            and c.created_at is not None and (c.updated_at - c.created_at).total_seconds() > 1,
            "is_story_author": c.user_id == author_id,
            "created_at": c.created_at,
            "user": c.user,
            "replies": [],
        }
        if c.parent_id:
            replies[c.parent_id].append(item)
        else:
            roots.append(item)
    for root in roots:
        root["replies"] = replies.get(root["id"], [])
    # Bỏ bình luận gốc đã xoá mà không còn trả lời nào
    roots = [r for r in roots if not (r["is_deleted"] and not r["replies"])]
    return list(reversed(roots))


def create_comment(db: Session, chapter: Chapter, user: User, data: CommentCreate) -> Comment:
    parent = None
    if data.parent_id is not None:
        parent = db.get(Comment, data.parent_id)
        if parent is None or parent.chapter_id != chapter.id:
            raise ValueError("Bình luận được trả lời không tồn tại")
        if parent.parent_id:  # chỉ 1 cấp trả lời: trả lời của trả lời -> gắn vào bình luận gốc
            parent = db.get(Comment, parent.parent_id)

    comment = Comment(
        chapter_id=chapter.id,
        user_id=user.id,
        parent_id=parent.id if parent else None,
        content=data.content.strip(),
    )
    db.add(comment)

    story = chapter.story
    link = f"/truyen/{story.id}/chuong/{chapter.id}#binh-luan"
    if parent and parent.user_id != user.id:
        notify(db, parent.user_id, "reply",
               f"{user.display_name} đã trả lời bình luận của bạn ở {story.title}, chương {chapter.number}", link)
    if story.author_id != user.id and (parent is None or parent.user_id != story.author_id):
        notify(db, story.author_id, "comment",
               f"{user.display_name} đã bình luận ở {story.title}, chương {chapter.number}", link)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment(db: Session, chapter: Chapter, comment_id: int) -> Comment | None:
    comment = db.get(Comment, comment_id)
    return comment if comment and comment.chapter_id == chapter.id and not comment.is_deleted else None


def update_comment(db: Session, comment: Comment, content: str) -> None:
    comment.content = content.strip()
    db.commit()


def delete_comment(db: Session, comment: Comment) -> None:
    """Xoá mềm: giữ chỗ để các trả lời không bị mất ngữ cảnh."""
    comment.is_deleted = True
    db.commit()


# ---------- Đánh giá ----------

def _refresh_rating_stats(db: Session, story: Story) -> None:
    avg, count = db.execute(
        select(func.avg(Rating.score), func.count(Rating.id)).where(Rating.story_id == story.id)
    ).one()
    story.rating_avg = round(float(avg or 0), 2)
    story.rating_count = count


def upsert_rating(db: Session, story: Story, user: User, data: RatingUpsert) -> Rating:
    if story.author_id == user.id:
        raise PermissionError("Bạn không thể tự đánh giá truyện của mình")
    rating = db.scalar(select(Rating).where(Rating.story_id == story.id, Rating.user_id == user.id))
    is_new = rating is None
    if is_new:
        rating = Rating(story_id=story.id, user_id=user.id)
        db.add(rating)
    rating.score = data.score
    rating.review = data.review.strip()
    db.flush()
    _refresh_rating_stats(db, story)
    if is_new:
        notify(db, story.author_id, "rating",
               f"{user.display_name} đã đánh giá {data.score} sao cho {story.title}", f"/truyen/{story.id}#danh-gia")
    db.commit()
    db.refresh(rating)
    return rating


def delete_rating(db: Session, story: Story, user: User) -> bool:
    rating = db.scalar(select(Rating).where(Rating.story_id == story.id, Rating.user_id == user.id))
    if rating is None:
        return False
    db.delete(rating)
    db.flush()
    _refresh_rating_stats(db, story)
    db.commit()
    return True


def rating_summary(db: Session, story: Story, skip: int, limit: int) -> dict:
    distribution = {s: 0 for s in range(5, 0, -1)}
    for score, count in db.execute(
        select(Rating.score, func.count()).where(Rating.story_id == story.id).group_by(Rating.score)
    ):
        distribution[score] = count
    items = list(
        db.scalars(
            select(Rating)
            .where(Rating.story_id == story.id)
            .options(selectinload(Rating.user))
            .order_by(Rating.updated_at.desc(), Rating.id.desc())
            .offset(skip)
            .limit(limit)
        )
    )
    return {
        "rating_avg": story.rating_avg,
        "rating_count": story.rating_count,
        "distribution": distribution,
        "items": items,
    }


# ---------- Theo dõi ----------

def _refresh_followers(db: Session, story: Story) -> None:
    story.follower_count = db.scalar(
        select(func.count()).select_from(Follow).where(Follow.story_id == story.id)
    )


def follow_story(db: Session, story: Story, user: User) -> None:
    if db.get(Follow, (user.id, story.id)) is None:
        db.add(Follow(user_id=user.id, story_id=story.id))
        db.flush()
        _refresh_followers(db, story)
        db.commit()


def unfollow_story(db: Session, story: Story, user: User) -> None:
    follow = db.get(Follow, (user.id, story.id))
    if follow is not None:
        db.delete(follow)
        db.flush()
        _refresh_followers(db, story)
        db.commit()


def followed_stories(db: Session, user: User) -> list[Story]:
    return list(
        db.scalars(
            select(Story)
            .join(Follow, Follow.story_id == Story.id)
            .where(Follow.user_id == user.id, Story.is_published.is_(True))
            .options(selectinload(Story.author), selectinload(Story.genres))
            .order_by(Story.updated_at.desc())
        )
    )
