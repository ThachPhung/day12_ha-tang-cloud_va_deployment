"""Monthly budget protection — state in Redis."""
from datetime import datetime

from fastapi import HTTPException

from app.config import settings
from app.redis_client import get_redis

PRICE_PER_1K_INPUT = 0.00015
PRICE_PER_1K_OUTPUT = 0.0006


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1000) * PRICE_PER_1K_INPUT + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT


def check_budget(user_id: str, estimated_cost: float) -> None:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"

    r = get_redis()
    current = float(r.get(key) or 0)
    if current + estimated_cost > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": round(current, 4),
                "budget_usd": settings.monthly_budget_usd,
            },
        )


def record_cost(user_id: str, cost: float) -> float:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    r = get_redis()
    total = r.incrbyfloat(key, cost)
    r.expire(key, 32 * 24 * 3600)
    return float(total)
