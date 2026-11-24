from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import PlagiarismReport, User
from app.schemas.plagiarism import ReindexResult, ReportOut, ReportStatus, ReportStatusUpdate
from app.services.plagiarism_service import list_reports, reindex_all, report_to_dict

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
    report.status = data.status
    db.commit()
    db.refresh(report)
    return report_to_dict(report, admin)


@router.post("/reindex", response_model=ReindexResult)
def reindex(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Lập chỉ mục lại toàn bộ chương (chạy 1 lần cho các chương đã có trước khi cài tính năng)."""
    return reindex_all(db)
