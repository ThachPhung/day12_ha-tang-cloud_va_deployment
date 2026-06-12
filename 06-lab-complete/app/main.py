"""Production AI Agent — Part 6 final project."""
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, estimate_cost, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import get_redis, ping_redis
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
HISTORY_TTL = 3600
MAX_HISTORY = 20


def _history_key(user_id: str) -> str:
    return f"history:{user_id}"


def load_history(user_id: str) -> list[dict]:
    raw = get_redis().lrange(_history_key(user_id), 0, -1)
    return [json.loads(item) for item in raw]


def append_history(user_id: str, role: str, content: str) -> list[dict]:
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    key = _history_key(user_id)
    r = get_redis()
    r.rpush(key, json.dumps(entry))
    r.ltrim(key, -MAX_HISTORY, -1)
    r.expire(key, HISTORY_TTL)
    return load_history(user_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    if not ping_redis():
        raise RuntimeError("Cannot connect to Redis")
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count
    start = time.time()
    _request_count += 1
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    if "server" in response.headers:
        del response.headers["server"]
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "ms": round((time.time() - start) * 1000, 1),
    }))
    return response


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default", min_length=1, max_length=64)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    user_id: str
    history_length: int
    timestamp: str


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "endpoints": {"ask": "POST /ask", "health": "GET /health", "ready": "GET /ready"},
    }


@app.post("/ask", response_model=AskResponse)
async def ask_agent(
    body: AskRequest,
    _key: str = Depends(verify_api_key),
):
    check_rate_limit(body.user_id)

    input_tokens = len(body.question.split()) * 2
    check_budget(body.user_id, estimate_cost(input_tokens, 0))

    history = load_history(body.user_id)
    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": body.user_id,
        "history_len": len(history),
    }))

    answer = llm_ask(body.question)
    updated = append_history(body.user_id, "user", body.question)
    updated = append_history(body.user_id, "assistant", answer)

    output_tokens = len(answer.split()) * 2
    record_cost(body.user_id, estimate_cost(input_tokens, output_tokens))

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        user_id=body.user_id,
        history_length=len(updated),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "redis": "ok" if ping_redis() else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not _is_ready or not ping_redis():
        raise HTTPException(503, "Not ready")
    return {"ready": True, "redis": True}


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
