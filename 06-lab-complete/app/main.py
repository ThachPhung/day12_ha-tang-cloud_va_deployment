"""
English Flashcard API — Part 6 (Day 12 production-ready)

Kết hợp:
  - English Flashcard backend (decks, cards, SRS study)
  - Day 12: health/ready, API key, rate limit, cost guard, Redis, JSON logging
"""
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import uvicorn

from app.api.routes import admin, auth as flashcard_auth, cards, decks, settings as user_settings, stats, study, users
from app.auth import verify_api_key
from app.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.cost_guard import check_budget, estimate_cost, record_cost
from app.models.user import User, UserRole
from app.rate_limiter import check_rate_limit
from app.redis_client import ping_redis
from app.services.auth_service import create_user_settings
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False


def seed_admin():
    """Tạo admin nếu chưa có. An toàn khi nhiều worker chạy cùng lúc."""
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            return
        admin_user = User(
            username="admin",
            email="admin@flashcard.local",
            password_hash=get_password_hash("admin1234"),
            display_name="Administrator",
            role=UserRole.admin,
        )
        db.add(admin_user)
        try:
            db.commit()
            db.refresh(admin_user)
            create_user_settings(db, admin_user.id)
        except IntegrityError:
            db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    if settings.environment == "production" and settings.AGENT_API_KEY == "dev-key-change-me":
        raise RuntimeError("AGENT_API_KEY must be set in production!")
    if not ping_redis():
        raise RuntimeError("Cannot connect to Redis")

    Base.metadata.create_all(bind=engine)
    seed_admin()
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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start = time.time()
    response: Response = await call_next(request)
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


# ── Flashcard API routes ──────────────────────────────────────
app.include_router(flashcard_auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(decks.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(study.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(user_settings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


# ── Day 12 ops + AI ask ─────────────────────────────────────────
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default", min_length=1, max_length=64)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    user_id: str
    timestamp: str


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "flashcard_api": "/api",
        "health": "/health",
        "ready": "/ready",
        "ask": "POST /ask (X-API-Key)",
    }


@app.post("/ask", response_model=AskResponse)
async def ask_english_tutor(body: AskRequest, _key: str = Depends(verify_api_key)):
    """AI English tutor — hỏi đáp tiếng Anh (mock LLM)."""
    check_rate_limit(body.user_id)
    tokens = len(body.question.split()) * 2
    check_budget(body.user_id, estimate_cost(tokens, 0))
    answer = llm_ask(body.question)
    record_cost(body.user_id, estimate_cost(tokens, len(answer.split()) * 2))
    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.LLM_MODEL,
        user_id=body.user_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
def health():
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if db_ok and ping_redis() else "degraded",
        "version": settings.app_version,
        "database": "ok" if db_ok else "error",
        "redis": "ok" if ping_redis() else "error",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    if not _is_ready or not ping_redis():
        raise HTTPException(503, "Not ready")
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        raise HTTPException(503, "Database not ready")
    return {"ready": True, "redis": True, "database": True}


@app.get("/api/health")
def api_health():
    return health()


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        timeout_graceful_shutdown=30,
    )
