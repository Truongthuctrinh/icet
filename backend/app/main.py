from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.redis_client import redis_client
from app.models import Genre
from app.models.genre import DEFAULT_GENRES
from app.routers import auth, chapters, community, plagiarism, reading, stories, trace


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
    yield


app = FastAPI(title="ICeT API", lifespan=lifespan)

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


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ok", "db": "ok", "redis": "ok"}
