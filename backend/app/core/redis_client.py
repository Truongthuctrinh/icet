from redis import Redis

from app.core.config import settings

# Một kết nối Redis dùng chung cho cả app (health check, rate limit, ...)
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
