from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    deck_id: int | None = None


class CardInSession(BaseModel):
    id: int
    deck_id: int
    front: str
    back: str
    phonetic: str | None
    part_of_speech: str | None
    example: str | None
    example_translation: str | None
    notes: str | None
    tags: str | None
    image_url: str | None
    audio_url: str | None
    status: str
    is_new: bool = False


class SessionResponse(BaseModel):
    id: int
    deck_id: int | None
    status: str
    total_cards: int
    completed_cards: int
    remaining_cards: int
    current_card: CardInSession | None = None


class AnswerRequest(BaseModel):
    card_id: int
    rating: str
    response_time_ms: int | None = None


class AnswerResponse(BaseModel):
    success: bool
    progress: dict
    session: dict


class SessionFinishResponse(BaseModel):
    id: int
    total_cards: int
    completed_cards: int
    duration_seconds: int
    ratings: dict
    remember_rate: float
