"""Merged config — English Flashcard + Day 12 production settings."""
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "flashcard.db"


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    APP_NAME: str = "English Flashcard API"
    APP_VERSION: str = "1.0.0"

    # Flashcard database
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,*"
    MAX_USERS: int = 5

    # Day 12 — API gateway
    AGENT_API_KEY: str = "dev-key-change-me"
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def agent_api_key(self) -> str:
        return self.AGENT_API_KEY

    @property
    def rate_limit_per_minute(self) -> int:
        return self.RATE_LIMIT_PER_MINUTE

    @property
    def monthly_budget_usd(self) -> float:
        return self.MONTHLY_BUDGET_USD

    @property
    def environment(self) -> str:
        return self.ENVIRONMENT

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_version(self) -> str:
        return self.APP_VERSION

    @property
    def log_level(self) -> str:
        return self.LOG_LEVEL

    @property
    def redis_url(self) -> str:
        return self.REDIS_URL

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return _normalize_database_url(value)

    class Config:
        env_file = ".env"


settings = Settings()
