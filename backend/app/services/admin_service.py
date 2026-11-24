import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.redis_client import redis_client
from app.models import Chapter, Comment, PlagiarismReport, Rating, ReadingSession, Story, User


def _count(db: Session, stmt) -> int:
    return db.scalar(stmt) or 0


def _since_24h() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=24)


def _redis_keys(pattern: str) -> list[str]:
    return list(redis_client.scan_iter(match=pattern, count=500))


def overview(db: Session) -> dict:
    count = lambda model, *where: _count(db, select(func.count()).select_from(model).where(*where))
    return {
        "users": count(User),
        "locked_users": count(User, User.is_active.is_(False)),
        "stories_published": count(Story, Story.is_published.is_(True)),
        "chapters_published": count(Chapter, Chapter.is_published.is_(True)),
        "reading_sessions_24h": count(ReadingSession, ReadingSession.created_at >= _since_24h()),
        "reading_sessions_total": count(ReadingSession),
        "comments": count(Comment, Comment.is_deleted.is_(False)),
        "ratings": count(Rating),
        "plagiarism_pending": count(PlagiarismReport, PlagiarismReport.status == "pending"),
        "plagiarism_confirmed": count(PlagiarismReport, PlagiarismReport.status == "confirmed"),
        "banned_ips": len(_redis_keys("ban:ip:*")),
        "bot_hits": sum(int(redis_client.get(k) or 0) for k in _redis_keys("bots:blocked:*")),
    }


def list_users(db: Session, q: str | None, skip: int, limit: int) -> list[dict]:
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc())
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.username.ilike(pattern), User.display_name.ilike(pattern), User.email.ilike(pattern)))
    users = list(db.scalars(stmt.offset(skip).limit(limit)))
    ids = [u.id for u in users]
    stories = dict(
        db.execute(select(Story.author_id, func.count()).where(Story.author_id.in_(ids)).group_by(Story.author_id)).all()
    ) if ids else {}
    sessions = dict(
        db.execute(
            select(ReadingSession.user_id, func.count())
            .where(ReadingSession.user_id.in_(ids), ReadingSession.created_at >= _since_24h())
            .group_by(ReadingSession.user_id)
        ).all()
    ) if ids else {}
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
            "story_count": stories.get(u.id, 0),
            "reading_sessions_24h": sessions.get(u.id, 0),
            "violations": int(redis_client.get(f"violations:user:{u.id}") or 0),
        }
        for u in users
    ]


def security_report(db: Session) -> dict:
    # Vi phạm: violations:<subject> (tổng) và violations:<subject>:<scope> (theo loại)
    totals: dict[str, int] = {}
    scopes: dict[str, dict[str, int]] = {}
    for key in _redis_keys("violations:*"):
        rest = key[len("violations:"):]
        parts = rest.split(":")
        value = int(redis_client.get(key) or 0)
        if len(parts) == 2:  # user:3 | ip:1.2.3.4
            totals[rest] = value
        elif parts[0] == "user" and len(parts) == 3:
            scopes.setdefault(f"user:{parts[1]}", {})[parts[2]] = value
        elif parts[0] == "ip":  # ip có thể chứa ":" (IPv6) -> phần cuối là loại vi phạm
            scopes.setdefault(":".join(parts[:-1]), {})[parts[-1]] = value

    user_ids = [int(s.split(":")[1]) for s in totals if s.startswith("user:")]
    names = {u.id: u for u in db.scalars(select(User).where(User.id.in_(user_ids)))} if user_ids else {}
    violations = []
    for subject, total in sorted(totals.items(), key=lambda kv: -kv[1]):
        item = {"subject": subject, "total": total, "by_scope": scopes.get(subject, {})}
        if subject.startswith("user:"):
            user = names.get(int(subject.split(":")[1]))
            if user:
                item.update(username=user.username, display_name=user.display_name)
        violations.append(item)

    bans = [
        {"ip": key[len("ban:ip:"):], "reason": redis_client.get(key) or "", "expires_in": max(redis_client.ttl(key), 0)}
        for key in _redis_keys("ban:ip:*")
    ]
    bot_hits = {key[len("bots:blocked:"):]: int(redis_client.get(key) or 0) for key in _redis_keys("bots:blocked:*")}
    load = lambda key: [json.loads(x) for x in redis_client.lrange(key, 0, 49)]
    return {
        "violations": violations,
        "bans": sorted(bans, key=lambda b: -b["expires_in"]),
        "honeypot_log": load("honeypot:log"),
        "bot_hits": dict(sorted(bot_hits.items(), key=lambda kv: -kv[1])),
        "bot_log": load("bots:log"),
    }


def unban_ip(ip: str) -> bool:
    return bool(redis_client.delete(f"ban:ip:{ip}"))


def clear_violations(subject: str) -> int:
    keys = [f"violations:{subject}", *_redis_keys(f"violations:{subject}:*")]
    return redis_client.delete(*keys) if keys else 0
