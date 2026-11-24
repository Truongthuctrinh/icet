from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.trace import TraceRequest, TraceResult
from app.services.trace_service import trace_text

router = APIRouter(prefix="/api/trace", tags=["trace"])


@router.post("", response_model=TraceResult)
def trace(
    data: TraceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dán đoạn văn nghi bị sao chép -> tìm phiên đọc đã làm lộ nội dung."""
    return trace_text(db, data.text, current_user)
