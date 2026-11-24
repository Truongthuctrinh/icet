from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StoryStatus = Literal["ongoing", "completed", "paused"]
StorySort = Literal["updated", "new", "rating", "followers"]


class GenreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class StoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    status: StoryStatus = "ongoing"
    genre_ids: list[int] = Field(default_factory=list, max_length=5)


class StoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: StoryStatus | None = None
    is_published: bool | None = None
    genre_ids: list[int] | None = Field(default=None, max_length=5)


class AuthorBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    is_published: bool
    created_at: datetime
    updated_at: datetime
    author: AuthorBrief
    genres: list[GenreOut]
    rating_avg: float
    rating_count: int
    follower_count: int


class MyRating(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: int
    review: str


class StoryDetailOut(StoryOut):
    """Trang chi tiết: thêm thông tin riêng của người đang xem (nếu đã đăng nhập)."""
    is_following: bool = False
    my_rating: MyRating | None = None
