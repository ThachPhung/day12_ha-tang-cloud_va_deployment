from datetime import datetime

from pydantic import BaseModel, Field


class DeckCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    front_language: str = "English"
    back_language: str = "Vietnamese"
    visibility: str = "private"
    new_cards_per_day: int = Field(default=20, ge=1, le=500)
    review_limit_per_day: int = Field(default=100, ge=1, le=1000)
    owner_id: int | None = None


class DeckUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    visibility: str | None = None
    new_cards_per_day: int | None = Field(None, ge=1, le=500)
    review_limit_per_day: int | None = Field(None, ge=1, le=1000)


class DeckResponse(BaseModel):
    id: int
    owner_id: int
    owner_name: str
    name: str
    description: str | None
    front_language: str
    back_language: str
    visibility: str
    new_cards_per_day: int
    review_limit_per_day: int
    card_count: int = 0
    due_count: int = 0
    new_count: int = 0
    progress_percent: float = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
