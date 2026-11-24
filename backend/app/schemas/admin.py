from datetime import datetime

from pydantic import BaseModel


class OverviewOut(BaseModel):
    users: int
    locked_users: int
    stories_published: int
    chapters_published: int
    reading_sessions_24h: int
    reading_sessions_total: int
    comments: int
    ratings: int
    plagiarism_pending: int
    plagiarism_confirmed: int
    banned_ips: int
    bot_hits: int


class AdminUserOut(BaseModel):
    id: int
    username: str
    display_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    story_count: int
    reading_sessions_24h: int
    violations: int


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None  # "user" | "admin"


class ViolationOut(BaseModel):
    subject: str  # "user:3" | "ip:1.2.3.4"
    total: int
    by_scope: dict[str, int]
    username: str | None = None
    display_name: str | None = None


class BanOut(BaseModel):
    ip: str
    reason: str
    expires_in: int  # giây


class SecurityOut(BaseModel):
    violations: list[ViolationOut]
    bans: list[BanOut]
    honeypot_log: list[dict]
    bot_hits: dict[str, int]
    bot_log: list[dict]
