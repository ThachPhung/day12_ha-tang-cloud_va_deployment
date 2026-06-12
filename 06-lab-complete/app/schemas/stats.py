from pydantic import BaseModel


class StatsOverview(BaseModel):
    due_today: int
    new_available: int
    total_studied: int
    mastered: int
    streak_days: int
    recent_decks: list[dict]


class DailyStats(BaseModel):
    date: str
    reviews: int
    new_cards: int
    good_easy_rate: float


class DeckStats(BaseModel):
    deck_id: int
    deck_name: str
    total_cards: int
    new_count: int
    learning_count: int
    review_count: int
    mastered_count: int
    suspended_count: int
    due_count: int
