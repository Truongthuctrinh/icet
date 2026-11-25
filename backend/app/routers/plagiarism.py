from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.task_queue import enqueue
from app.models import Chapter, PlagiarismReport, User
from app.schemas.plagiarism import ReindexResult, ReportOut, ReportStatus, ReportStatusUpdate
from app.services.plagiarism_service import apply_confirmation, list_reports, reindex_all, report_to_dict

router = APIRouter(prefix="/api/plagiarism", tags=["plagiarism"])


@router.get("/reports", response_model=list[ReportOut])
def get_reports(
    status_filter: ReportStatus | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_reports(db, current_user, status_filter)


@router.patch("/reports/{report_id}", response_model=ReportOut)
def update_report_status(
    report_id: int,
    data: ReportStatusUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    report = db.get(PlagiarismReport, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cảnh báo")
    was_confirmed = report.status == "confirmed"
    report.status = data.status
    if data.status == "confirmed" and not was_confirmed:
        apply_confirmation(db, report)
    db.commit()
    db.refresh(report)
    return report_to_dict(report, admin)


@router.post("/reindex", response_model=ReindexResult)
async def reindex(request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Lập chỉ mục lại toàn bộ chương (chạy 1 lần cho dữ liệu cũ, hoặc sau khi đổi model/ngưỡng).
    Có worker -> giao cho worker (có so theo nghĩa); không có -> chạy ngay, chỉ MinHash."""
    if await enqueue(request.app, "reindex_job"):
        total = db.scalar(select(func.count(Chapter.id))) or 0
        return {"chapters": total, "reports": -1, "queued": True}
    return await run_in_threadpool(reindex_all, db)
