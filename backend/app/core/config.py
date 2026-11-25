from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]  # thư mục icet/
BACKEND_DIR = Path(__file__).resolve().parents[2]  # thư mục icet/backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    READ_TOKEN_EXPIRE_MINUTES: int = 30
    MAX_PARAGRAPHS_PER_REQUEST: int = 10

    RATE_OPEN_CHAPTER_PER_MIN: int = 10
    RATE_PARAGRAPHS_PER_MIN: int = 60
    RATE_LOGIN_PER_5MIN: int = 5
    RATE_COMMENT_PER_MIN: int = 5

    # Chỉ tin header X-Forwarded-For khi request đi qua các proxy này (Vite dev server, nginx...)
    TRUSTED_PROXIES: str = "127.0.0.1,::1"
    HONEYPOT_BAN_MINUTES: int = 30

    # Hàng đợi việc nền (arq trên Redis). Tắt -> kiểm tra đạo văn chạy ngay trong API (chỉ MinHash)
    TASK_QUEUE_ENABLED: bool = True

    # Phát hiện viết lại (paraphrase) bằng embedding — chạy trong worker
    EMBEDDING_ENABLED: bool = True
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_CACHE_DIR: str = ""  # để trống = thư mục cache mặc định của fastembed
    SEMANTIC_THRESHOLD: float = 0.65  # cosine >= ngưỡng -> cùng ý. Đo bằng calibrate_embedding: viết lại >=0,75, cùng chủ đề <=0,53
    SEMANTIC_MIN_WORDS: int = 12  # đoạn ngắn hơn không đưa vào so sánh ngữ nghĩa

    # Ảnh tải lên (bìa truyện, ảnh đại diện)
    MEDIA_DIR: str = ""  # để trống = icet/backend/media
    MAX_UPLOAD_MB: int = 2
    RATE_UPLOAD_PER_MIN: int = 10

    @property
    def media_path(self) -> Path:
        return Path(self.MEDIA_DIR) if self.MEDIA_DIR else BACKEND_DIR / "media"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
