# backend/app/core/redis_client.py
import redis.asyncio as aioredis
from app.core.config import settings

REDIS_URL = settings.REDIS_URL
_redis = None


def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=False)
    return _redis
