from redis.asyncio import Redis
from .config import settings

redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
