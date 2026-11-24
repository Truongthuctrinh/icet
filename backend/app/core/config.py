from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]  # thư mục icet/


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

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
