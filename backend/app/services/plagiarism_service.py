"""Phát hiện đạo văn giữa các chương trên ICeT.

Luồng xử lý khi 1 chương được lưu (chạy nền, không làm chậm thao tác lưu):
  1. Lập chỉ mục LSH cho từng đoạn của chương.
  2. Tìm các đoạn ở chương khác rơi vào cùng xô LSH -> ứng viên.
  3. Tính Jaccard chính xác cho từng cặp ứng viên, giữ cặp >= PARAGRAPH_THRESHOLD.
  4. Với mỗi đoạn, xác định ai viết TRƯỚC (lần xuất hiện sớm nhất trong các chương của từng tác giả).
     Người viết sau là "suspect", bản sớm nhất là "source". Cùng tác giả thì không tính.
     Tỉ lệ chữ bị trùng >= REPORT_THRESHOLD -> tạo/cập nhật cảnh báo; hết trùng -> tự gỡ cảnh báo.
"""
import logging
from collections import defaultdict

from sqlalchemy import delete, select, tuple_
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.minhash import MIN_SHINGLES, band_buckets, jaccard, shingles, signature
from app.core.watermark import extract_session_ids, strip_marks
from app.models import Chapter, ParagraphLSH, PlagiarismReport
from app.services.notification_service import notify

logger = logging.getLogger("icet.plagiarism")

PARAGRAPH_THRESHOLD = 0.5  # 2 đoạn giống nhau >= 50% shingle -> coi là trùng
REPORT_THRESHOLD = 0.15  # >= 15% số chữ của chương bị trùng -> tạo cảnh báo


def split_paragraphs(content: str) -> list[str]:
    return content.split("\n\n") if content else []


def index_chapter(db: Session, chapter: Chapter) -> dict[int, set[str]]:
    """Ghi lại chỉ mục LSH của chương. Trả về {chỉ số đoạn: tập shingle} của các đoạn đủ dài."""
    db.execute(delete(ParagraphLSH).where(ParagraphLSH.chapter_id == chapter.id))
    indexed: dict[int, set[str]] = {}
    rows = []
    for idx, paragraph in enumerate(split_paragraphs(chapter.content)):
        sh = shingles(paragraph)
        if len(sh) < MIN_SHINGLES:
            continue
        indexed[idx] = sh
        for band, bucket in band_buckets(signature(sh)):
            rows.append(
                ParagraphLSH(chapter_id=chapter.id, paragraph_index=idx, band=band, bucket=bucket)
            )
    db.add_all(rows)
    db.flush()
    return indexed


def _find_candidates(db: Session, chapter: Chapter, indexed: dict[int, set[str]]):
    """{chapter_id khác: {(đoạn của mình, đoạn của họ)}} — xét mọi chương khác, kể cả của chính tác giả
    (chương cũ của chính mình dùng để xác định đoạn văn là của ai viết trước)."""
    my_buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
    for idx, sh in indexed.items():
        for key in band_buckets(signature(sh)):
            my_buckets[key].append(idx)
    if not my_buckets:
        return {}

    stmt = select(
        ParagraphLSH.chapter_id, ParagraphLSH.paragraph_index, ParagraphLSH.band, ParagraphLSH.bucket
    ).where(
        tuple_(ParagraphLSH.band, ParagraphLSH.bucket).in_(list(my_buckets.keys())),
        ParagraphLSH.chapter_id != chapter.id,
    )
    candidates: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for other_chapter_id, other_idx, band, bucket in db.execute(stmt):
        for my_idx in my_buckets[(band, bucket)]:
            candidates[other_chapter_id].add((my_idx, other_idx))
    return candidates


def _word_count(text: str) -> int:
    return len(text.split())


def _upsert_report(db: Session, suspect: Chapter, source: Chapter, pairs: list[dict]) -> PlagiarismReport | None:
    """pairs: [{suspect_index, source_index, similarity}]. Tính tỉ lệ trùng theo chương suspect."""
    suspect_paragraphs = split_paragraphs(suspect.content)
    total_words = sum(_word_count(p) for p in suspect_paragraphs) or 1
    matched_suspect = {p["suspect_index"] for p in pairs}
    matched_words = sum(_word_count(suspect_paragraphs[i]) for i in matched_suspect)
    score = round(matched_words / total_words, 4)

    report = db.scalar(
        select(PlagiarismReport).where(
            PlagiarismReport.suspect_chapter_id == suspect.id,
            PlagiarismReport.source_chapter_id == source.id,
        )
    )
    if score < REPORT_THRESHOLD:
        # Đã sửa hết phần trùng -> gỡ cảnh báo đang chờ duyệt (giữ lại cảnh báo admin đã xử lý)
        if report and report.status == "pending":
            db.delete(report)
        return None

    _, session_ids = extract_session_ids(suspect.content)
    if report is None:
        report = PlagiarismReport(suspect_chapter_id=suspect.id, source_chapter_id=source.id)
        db.add(report)
        # Cảnh báo mới -> báo cho cả 2 tác giả
        percent = round(score * 100)
        notify(db, source.story.author_id, "plagiarism_source",
               f"Truyện {source.story.title} của bạn có thể đã bị sao chép ({percent}% nội dung một chương)",
               "/tac-gia/dao-van")
        notify(db, suspect.story.author_id, "plagiarism_suspect",
               f"Chương {suspect.number} của {suspect.story.title} trùng {percent}% với truyện của tác giả khác",
               "/tac-gia/dao-van")
    report.score = score
    report.matched_count = len(matched_suspect)
    report.matches = sorted(pairs, key=lambda p: p["suspect_index"])
    report.watermark_sessions = session_ids
    return report


def _order(chapter: Chapter) -> tuple:
    """Thứ tự thời gian: chương nào tạo trước thì "nhỏ" hơn."""
    return (chapter.created_at, chapter.id)


def check_chapter(db: Session, chapter_id: int) -> list[PlagiarismReport]:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        return []
    author_id = chapter.story.author_id

    indexed = index_chapter(db, chapter)
    candidates = _find_candidates(db, chapter, indexed)

    # 1. Xác nhận bằng Jaccard chính xác: matches[đoạn của mình] = [(chương khác, đoạn của họ, độ giống)]
    matches: dict[int, list[tuple[Chapter, int, float]]] = defaultdict(list)
    for other_id, pairs in candidates.items():
        other = db.get(Chapter, other_id)
        other_paragraphs = split_paragraphs(other.content)
        for my_idx, other_idx in pairs:
            sim = jaccard(indexed[my_idx], shingles(other_paragraphs[other_idx]))
            if sim >= PARAGRAPH_THRESHOLD:
                matches[my_idx].append((other, other_idx, round(sim, 3)))

    # 2. Với từng đoạn: tìm lần xuất hiện SỚM NHẤT trong các chương của chính tác giả này
    #    -> đó là "thời điểm tác giả viết đoạn này". So với chương của tác giả khác để biết ai chép ai.
    #    report_pairs[(suspect_id, source_id)] = {đoạn suspect: {suspect_index, source_index, similarity}}
    report_pairs: dict[tuple[int, int], dict[int, dict]] = defaultdict(dict)
    chapters_by_id: dict[int, Chapter] = {chapter.id: chapter}

    def add_pair(suspect: Chapter, s_idx: int, source: Chapter, src_idx: int, sim: float):
        chapters_by_id[suspect.id] = suspect
        chapters_by_id[source.id] = source
        bucket = report_pairs[(suspect.id, source.id)]
        if s_idx not in bucket or sim > bucket[s_idx]["similarity"]:
            bucket[s_idx] = {"suspect_index": s_idx, "source_index": src_idx, "similarity": sim}

    for my_idx, found in matches.items():
        own = [m for m in found if m[0].story.author_id == author_id]
        others = [m for m in found if m[0].story.author_id != author_id]
        origin_key = min([_order(chapter)] + [_order(m[0]) for m in own])
        i_am_origin = origin_key == _order(chapter)

        earlier = [m for m in others if _order(m[0]) < origin_key]
        if earlier:
            # Người khác viết trước -> chương này nghi đạo, nguồn là bản sớm nhất
            src, src_idx, sim = min(earlier, key=lambda m: _order(m[0]))
            add_pair(chapter, my_idx, src, src_idx, sim)
        elif i_am_origin:
            # Chương này là bản gốc -> các chương của người khác đăng sau là nghi đạo
            for other, other_idx, sim in others:
                add_pair(other, other_idx, chapter, my_idx, sim)
        # Còn lại: tác giả đã viết đoạn này ở chương cũ hơn -> chương cũ đó chịu trách nhiệm cảnh báo

    # 3. Ghi cảnh báo
    reports = []
    for (suspect_id, source_id), by_idx in report_pairs.items():
        report = _upsert_report(
            db, chapters_by_id[suspect_id], chapters_by_id[source_id], list(by_idx.values())
        )
        if report:
            reports.append(report)

    # 4. Gỡ các cảnh báo cũ (đang chờ duyệt) mà lần kiểm tra này không còn thấy trùng
    stale = db.scalars(
        select(PlagiarismReport).where(
            PlagiarismReport.status == "pending",
            (PlagiarismReport.suspect_chapter_id == chapter.id)
            | (PlagiarismReport.source_chapter_id == chapter.id),
        )
    )
    still_valid = set(report_pairs.keys())
    for old in stale:
        if (old.suspect_chapter_id, old.source_chapter_id) not in still_valid:
            db.delete(old)

    db.commit()
    return reports


def run_check_in_background(chapter_id: int) -> None:
    """Gọi từ BackgroundTasks của FastAPI: mở phiên DB riêng, lỗi thì chỉ ghi log."""
    db = SessionLocal()
    try:
        reports = check_chapter(db, chapter_id)
        if reports:
            logger.warning("Chương %s: phát hiện %d cảnh báo đạo văn", chapter_id, len(reports))
    except Exception:
        db.rollback()
        logger.exception("Lỗi khi kiểm tra đạo văn chương %s", chapter_id)
    finally:
        db.close()


def reindex_all(db: Session) -> dict:
    """Lập chỉ mục + kiểm tra lại toàn bộ chương (dùng 1 lần cho dữ liệu cũ)."""
    ids = list(db.scalars(select(Chapter.id).order_by(Chapter.created_at, Chapter.id)))
    report_ids: set[int] = set()
    for chapter_id in ids:
        report_ids.update(report.id for report in check_chapter(db, chapter_id))
    return {"chapters": len(ids), "reports": len(report_ids)}


# ---------- Đọc cảnh báo cho API ----------

def _chapter_ref(chapter: Chapter) -> dict:
    story = chapter.story
    return {
        "chapter_id": chapter.id,
        "chapter_number": chapter.number,
        "chapter_title": chapter.title,
        "story_id": story.id,
        "story_title": story.title,
        "author_username": story.author.username,
        "author_display_name": story.author.display_name,
        "created_at": chapter.created_at,
    }


def report_to_dict(report: PlagiarismReport, viewer) -> dict:
    suspect = report.suspect_chapter
    source = report.source_chapter
    suspect_paragraphs = split_paragraphs(suspect.content)
    source_paragraphs = split_paragraphs(source.content)

    if viewer.role == "admin":
        role = "admin"
    elif source.story.author_id == viewer.id:
        role = "source"
    else:
        role = "suspect"

    return {
        "id": report.id,
        "score": report.score,
        "matched_count": report.matched_count,
        "status": report.status,
        "my_role": role,
        "suspect": _chapter_ref(suspect),
        "source": _chapter_ref(source),
        "matches": [
            {
                **m,
                "suspect_text": strip_marks(suspect_paragraphs[m["suspect_index"]]),
                "source_text": strip_marks(source_paragraphs[m["source_index"]]),
            }
            for m in report.matches
            if m["suspect_index"] < len(suspect_paragraphs) and m["source_index"] < len(source_paragraphs)
        ],
        "watermark_sessions": report.watermark_sessions or [],
        "created_at": report.created_at,
        "updated_at": report.updated_at,
    }


def list_reports(db: Session, viewer, status: str | None = None) -> list[dict]:
    """Admin thấy tất cả; tác giả thấy cảnh báo liên quan đến truyện của mình (bị chép hoặc bị nghi)."""
    stmt = select(PlagiarismReport).order_by(PlagiarismReport.updated_at.desc())
    if status:
        stmt = stmt.where(PlagiarismReport.status == status)
    result = []
    for report in db.scalars(stmt):
        involved = {report.suspect_chapter.story.author_id, report.source_chapter.story.author_id}
        if viewer.role == "admin" or viewer.id in involved:
            result.append(report_to_dict(report, viewer))
    return result


def apply_confirmation(db: Session, report: PlagiarismReport) -> None:
    """Admin xác nhận đạo văn: ẩn chương vi phạm (khoá xuất bản lại) + báo cho 2 tác giả."""
    suspect = report.suspect_chapter
    source = report.source_chapter
    suspect.is_published = False
    notify(db, suspect.story.author_id, "plagiarism_confirmed",
           f"Chương {suspect.number} của {suspect.story.title} đã bị ẩn vì được xác nhận sao chép "
           f"từ {source.story.title}. Liên hệ quản trị viên nếu đây là nhầm lẫn.", "/tac-gia/dao-van")
    notify(db, source.story.author_id, "plagiarism_confirmed",
           f"Quản trị viên đã xác nhận {suspect.story.title} sao chép truyện {source.story.title} của bạn. "
           f"Chương vi phạm đã bị ẩn.", "/tac-gia/dao-van")


def locked_chapter_ids(db: Session, chapter_ids: list[int]) -> set[int]:
    """Các chương đang bị khoá vì có cảnh báo đạo văn đã xác nhận."""
    if not chapter_ids:
        return set()
    return set(
        db.scalars(
            select(PlagiarismReport.suspect_chapter_id).where(
                PlagiarismReport.status == "confirmed",
                PlagiarismReport.suspect_chapter_id.in_(chapter_ids),
            )
        )
    )
