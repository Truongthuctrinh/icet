from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StoryStatus = Literal["ongoing", "completed", "paused"]


class StoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    status: StoryStatus = "ongoing"


class StoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: StoryStatus | None = None
    is_published: bool | None = None


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