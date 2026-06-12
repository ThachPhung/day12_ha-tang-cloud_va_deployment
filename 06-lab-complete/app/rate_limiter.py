"""Redis-backed sliding window rate limiter."""
import time

from fastapi import HTTPException

from app.config import settings
from app.redis_client import get_redis


def check_rate_limit(user_id: str) -> None:
    now = time.time()
    window_start = now - 60
    key = f"rate:{user_id}"

    r = get_redis()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, 120)
    _, count, *_ = pipe.execute()

    if count >= settings.rate_limit_per_minute:
        r.zrem(key, str(now))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
