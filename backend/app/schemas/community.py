from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.story import AuthorBrief, StoryOut


# ---------- Bình luận ----------

class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class CommentOut(BaseModel):
    id: int
    content: str  # rỗng nếu đã xoá
    is_deleted: bool
    is_edited: bool
    is_story_author: bool  # người bình luận là tác giả truyện -> hiện nhãn "Tác giả"
    created_at: datetime
    user: AuthorBrief
    replies: list["CommentOut"] = []


# ---------- Đánh giá ----------

class RatingUpsert(BaseModel):
    score: int = Field(ge=1, le=5)
    review: str = Field(default="", max_length=2000)


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score: int
    review: str
    created_at: datetime
    updated_at: datetime
    user: AuthorBrief


class RatingSummary(BaseModel):
    rating_avg: float
    rating_count: int
    distribution: dict[int, int]  # {5: 12, 4: 3, ...}
    items: list[RatingOut]


# ---------- Theo dõi ----------

class FollowState(BaseModel):
    is_following: bool
    follower_count: int


# ---------- Thông báo ----------

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    message: str
    link: str
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int


# ---------- Hồ sơ tác giả ----------

class ProfileOut(BaseModel):
    username: str
    display_name: str
    avatar_url: str | None = None
    created_at: datetime
    story_count: int
    total_followers: int
    stories: list[StoryOut]
