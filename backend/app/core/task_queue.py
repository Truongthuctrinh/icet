"""Đưa việc nặng (kiểm tra đạo văn + embedding) sang worker arq chạy riêng.

API chỉ ghi 1 dòng vào hàng đợi trên Redis rồi trả lời ngay. Worker (app/worker.py) lấy việc ra làm.
Không kết nối được hàng đợi (chưa bật worker, đang chạy test...) -> chạy ngay trong API,
chỉ so nguyên văn bằng MinHash (không nạp model embedding vào API).
"""
import logging

from fastapi import FastAPI
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger("icet.queue")


async def open_pool(app: FastAPI) -> None:
    app.state.arq = None
    if not settings.TASK_QUEUE_ENABLED:
        return
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        app.state.arq = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    except Exception:
        logger.exception("Không mở được hàng đợi arq, kiểm tra đạo văn sẽ chạy ngay trong API")


async def close_pool(app: FastAPI) -> None:
    pool = getattr(app.state, "arq", None)
    if pool is not None:
        await pool.aclose()


async def enqueue(app: FastAPI, job: str, *args) -> bool:
    """True nếu đã đưa vào hàng đợi; False nếu không có hàng đợi / Redis lỗi."""
    pool = getattr(app.state, "arq", None)
    if pool is None:
        return False
    try:
        await pool.enqueue_job(job, *args)
        return True
    except Exception:
        logger.exception("Không đưa được việc %s vào hàng đợi", job)
        return False


async def schedule_plagiarism_check(app: FastAPI, chapter_id: int) -> None:
    """Dùng làm BackgroundTask sau khi tạo/sửa chương."""
    if await enqueue(app, "check_chapter_job", chapter_id):
        return
    from app.services.plagiarism_service import run_check_in_background

    await run_in_threadpool(run_check_in_background, chapter_id)
