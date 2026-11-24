from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.redis_client import redis_client
from app.routers import auth, chapters, reading, stories, trace

app = FastAPI(title="ICeT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(stories.router)
app.include_router(chapters.router)
app.include_router(reading.router)
app.include_router(trace.router)


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    redis_client.ping()
    return {"status": "ok", "db": "ok", "redis": "ok"}