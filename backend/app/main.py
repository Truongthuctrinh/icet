from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.redis_client import redis_client
from app.core.shield import HONEYPOT_PATHS, shield_middleware
from app.core.task_queue import close_pool, open_pool
from app.models import Genre
from app.models.genre import DEFAULT_GENRES
from app.routers import admin, auth, chapters, community, plagiarism, reading, stories, trace


def seed_genres() -> None:
    """Thêm danh sách thể loại mặc định nếu bảng genres còn trống."""
    db = SessionLocal()
    try:
        if db.scalar(select(Genre.id).limit(1)) is None:
            db.add_all(Genre(slug=slug, name=name) for slug, name in DEFAULT_GENRES)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_genres()
    await open_pool(app)  # hàng đợi việc nền (worker arq)
    yield
    await close_pool(app)


app = FastAPI(title="ICeT API", lifespan=lifespan)

app.middleware("http")(shield_middleware)  # chặn bot AI, honeypot, IP bị cấm + header bảo mật
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(stories.genre_router)
app.include_router(stories.router)
app.include_router(chapters.router)
app.include_router(reading.router)
app.include_router(community.router)
app.include_router(trace.router)
app.include_router(plagiarism.router)
app.include_router(admin.router)

AI_CRAWLERS = ["GPTBot", "ChatGPT-User", "OAI-SearchBot", "CCBot", "ClaudeBot", "Claude-Web", "anthropic-ai",
               "Google-Extended", "PerplexityBot", "Bytespider", "Amazonbot", "Applebot-Extended",
               "meta-externalagent", "FacebookBot", "Diffbot", "cohere-ai"]


@app.get("/robots.txt", response_class=PlainTextResponse, include_in_schema=False)
def robots():
    lines = [f"User-agent: {bot}\nDisallow: /\n" for bot in AI_CRAWLERS]
    lines.append("User-agent: *\n" + "".join(f"Disallow: {p}\n" for p in sorted(HONEYPOT_PATHS)))
    return "\n".join(lines)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ok", "db": "ok", "redis": "ok"}
