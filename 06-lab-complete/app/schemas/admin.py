from datetime import datetime

from pydantic import BaseModel


class MemberDeckProgress(BaseModel):
    deck_id: int
    deck_name: str
    owner_name: str
    visibility: str
    total_cards: int
    new_count: int
    learning_count: int
    review_count: int
    mastered_count: int
    due_count: int
    progress_percent: float


class MemberProgressReport(BaseModel):
    user_id: int
    username: str
    display_name: str
    due_today: int
    new_available: int
    total_studied: int
    mastered: int
    streak_days: int
    last_login_at: datetime | None
    decks: list[MemberDeckProgress]
