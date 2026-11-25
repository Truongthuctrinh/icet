from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.images import ImageError
from app.core.rate_limit import limit_by_user
from app.models import Story, User
from app.routers.stories import get_owned_story
from app.schemas.story import StoryOut
from app.schemas.user import UserOut
from app.services.media_service import delete_image, save_image

router = APIRouter(tags=["uploads"])
upload_limit = [Depends(limit_by_user("upload", settings.RATE_UPLOAD_PER_MIN, 60))]


async def read_limited(file: UploadFile) -> bytes:
    """Đọc tối đa MAX_UPLOAD_MB; file lớn hơn bị từ chối mà không đọc hết vào RAM."""
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"Ảnh tối đa {settings.MAX_UPLOAD_MB} MB")
    if not raw:
        raise HTTPException(422, "Chưa chọn ảnh")
    return raw


def store(raw: bytes, kind: str) -> str:
    try:
        return save_image(raw, kind)
    except ImageError as e:
        raise HTTPException(422, str(e))


@router.put("/api/stories/{story_id}/cover", response_model=StoryOut, dependencies=upload_limit)
async def upload_cover(
    file: UploadFile = File(...),
    story: Story = Depends(get_owned_story),
    db: Session = Depends(get_db),
):
    new_url = store(await read_limited(file), "cover")
    old_url, story.cover_url = story.cover_url, new_url
    db.commit()
    db.refresh(story)
    delete_image(old_url)  # xoá ảnh cũ SAU khi lưu DB thành công
    return story


@router.delete("/api/stories/{story_id}/cover", response_model=StoryOut)
def remove_cover(story: Story = Depends(get_owned_story), db: Session = Depends(get_db)):
    old_url, story.cover_url = story.cover_url, None
    db.commit()
    db.refresh(story)
    delete_image(old_url)
    return story


@router.put("/api/users/me/avatar", response_model=UserOut, dependencies=upload_limit)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_url = store(await read_limited(file), "avatar")
    user = current_user  # cùng phiên DB với get_db nên sửa trực tiếp được
    old_url, user.avatar_url = user.avatar_url, new_url
    db.commit()
    db.refresh(user)
    delete_image(old_url)
    return user


@router.delete("/api/users/me/avatar", response_model=UserOut)
def remove_avatar(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = current_user  # cùng phiên DB với get_db nên sửa trực tiếp được
    old_url, user.avatar_url = user.avatar_url, None
    db.commit()
    db.refresh(user)
    delete_image(old_url)
    return user
