from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Chapter, Follow, Notification


def notify(db: Session, user_id: int, kind: str, message: str, link: str = "") -> None:
    """Thêm 1 thông báo (chưa commit: để đi chung giao dịch với hành động gây ra nó)."""
    db.add(Notification(user_id=user_id, kind=kind, message=message[:300], link=link[:300]))


def notify_new_chapter(db: Session, chapter: Chapter) -> int:
    """Gửi thông báo cho mọi người theo dõi truyện (trừ chính tác giả). Trả về số người nhận."""
    story = chapter.story
    follower_ids = list(
        db.scalars(
            select(Follow.user_id).where(
                Follow.story_id == story.id, Follow.user_id != story.author_id
            )
        )
    )
    message = f"{story.title} vừa có chương {chapter.number}: {chapter.title}"
    link = f"/truyen/{story.id}/chuong/{chapter.id}"
    db.add_all(
        Notification(user_id=uid, kind="new_chapter", message=message, link=link)
        for uid in follower_ids
    )
    return len(follower_ids)


def list_notifications(db: Session, user_id: int, unread_only: bool, limit: int) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    return list(db.scalars(stmt.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)))


def unread_count(db: Session, user_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
    )


def mark_read(db: Session, user_id: int, notification_id: int) -> bool:
    result = db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount > 0


def mark_all_read(db: Session, user_id: int) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return result.rowcount
