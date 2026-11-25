"""Worker chạy việc nền của ICeT (kiểm tra đạo văn nguyên văn + theo nghĩa).

Chạy trong 1 terminal riêng (đã activate venv, đứng ở thư mục backend):
    arq app.worker.WorkerSettings
Lần đầu chạy sẽ tải model embedding (~220 MB) về máy, các lần sau dùng lại.
"""
import asyncio
import logging

from arq.connections import RedisSettings

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.embedder import load_embedder
from app.services.plagiarism_service import reindex_all, run_check_in_background

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("icet.worker")


async def startup(ctx: dict) -> None:
    # Nạp model 1 lần duy nhất; chạy trong thread để không chặn vòng lặp sự kiện
    ctx["embedder"] = await asyncio.to_thread(load_embedder)
    mode = "MinHash + embedding" if ctx["embedder"] else "chỉ MinHash"
    logger.info("Worker sẵn sàng (%s)", mode)


async def check_chapter_job(ctx: dict, chapter_id: int) -> None:
    await asyncio.to_thread(run_check_in_background, chapter_id, ctx.get("embedder"))


def _reindex(embedder) -> dict:
    db = SessionLocal()
    try:
        return reindex_all(db, embedder)
    finally:
        db.close()


async def reindex_job(ctx: dict) -> dict:
    result = await asyncio.to_thread(_reindex, ctx.get("embedder"))
    logger.info("Lập chỉ mục lại xong: %s", result)
    return result


class WorkerSettings:
    functions = [check_chapter_job, reindex_job]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 1  # máy yếu: làm từng việc một, model không bị nạp/chạy song song
    job_timeout = 600  # lập chỉ mục lại toàn bộ có thể lâu
    keep_result = 300
