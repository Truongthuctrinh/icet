from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.models import User
from app.schemas.admin import AdminUserOut, AdminUserUpdate, OverviewOut, SecurityOut
from app.services import admin_service as svc

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/overview", response_model=OverviewOut)
def overview(db: Session = Depends(get_db)):
    return svc.overview(db)


@router.get("/users", response_model=list[AdminUserOut])
def users(
    q: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return svc.list_users(db, q, skip, limit)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy người dùng")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự khoá hoặc tự đổi quyền của chính mình")
    if data.role is not None:
        if data.role not in ("user", "admin"):
            raise HTTPException(422, "Quyền không hợp lệ")
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    return next(u for u in svc.list_users(db, user.username, 0, 50) if u["id"] == user.id)


@router.get("/security", response_model=SecurityOut)
def security(db: Session = Depends(get_db)):
    return svc.security_report(db)


@router.delete("/security/bans/{ip}", status_code=status.HTTP_204_NO_CONTENT)
def unban(ip: str):
    if not svc.unban_ip(ip):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "IP này không bị cấm")


@router.delete("/security/violations/{subject}", status_code=status.HTTP_204_NO_CONTENT)
def clear_violations(subject: str):
    svc.clear_violations(subject)
