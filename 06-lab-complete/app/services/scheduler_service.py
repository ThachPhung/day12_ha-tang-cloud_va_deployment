import math
from datetime import datetime, timedelta, timezone

from app.models.progress import CardStatus, Rating, UserCardProgress

MASTERED_THRESHOLD_DAYS = 30


def apply_rating(progress: UserCardProgress, rating: Rating, now: datetime | None = None) -> UserCardProgress:
    """Apply SRS V1 algorithm to update progress after a review."""
    now = now or datetime.now(timezone.utc)

    if progress.status == CardStatus.NEW or progress.status == CardStatus.LEARNING:
        _apply_new_card_rating(progress, rating, now)
    else:
        _apply_review_card_rating(progress, rating, now)

    progress.last_rating = rating
    progress.last_reviewed_at = now
    progress.updated_at = now

    if progress.interval_days >= MASTERED_THRESHOLD_DAYS and progress.status in (
        CardStatus.REVIEW,
        CardStatus.MASTERED,
    ):
        progress.status = CardStatus.MASTERED

    return progress


def _apply_new_card_rating(progress: UserCardProgress, rating: Rating, now: datetime) -> None:
    if rating == Rating.AGAIN:
        progress.status = CardStatus.LEARNING
        progress.due_at = now + timedelta(minutes=1)
        progress.lapses = (progress.lapses or 0) + 1
    elif rating == Rating.HARD:
        progress.status = CardStatus.LEARNING
        progress.due_at = now + timedelta(minutes=6)
    elif rating == Rating.GOOD:
        progress.status = CardStatus.REVIEW
        progress.interval_days = 1
        progress.due_at = now + timedelta(days=1)
        progress.repetitions = (progress.repetitions or 0) + 1
    elif rating == Rating.EASY:
        progress.status = CardStatus.REVIEW
        progress.interval_days = 4
        progress.due_at = now + timedelta(days=4)
        progress.repetitions = (progress.repetitions or 0) + 1


def _apply_review_card_rating(progress: UserCardProgress, rating: Rating, now: datetime) -> None:
    interval = progress.interval_days or 1

    if rating == Rating.AGAIN:
        progress.status = CardStatus.LEARNING
        progress.due_at = now + timedelta(minutes=10)
        progress.interval_days = 1
        progress.lapses = (progress.lapses or 0) + 1
    elif rating == Rating.HARD:
        progress.status = CardStatus.REVIEW
        progress.interval_days = math.ceil(interval * 1.2)
        progress.due_at = now + timedelta(days=progress.interval_days)
        progress.repetitions = (progress.repetitions or 0) + 1
    elif rating == Rating.GOOD:
        progress.status = CardStatus.REVIEW
        progress.interval_days = math.ceil(interval * 2.5)
        progress.due_at = now + timedelta(days=progress.interval_days)
        progress.repetitions = (progress.repetitions or 0) + 1
    elif rating == Rating.EASY:
        progress.status = CardStatus.REVIEW
        progress.interval_days = math.ceil(interval * 3.5)
        progress.due_at = now + timedelta(days=progress.interval_days)
        progress.repetitions = (progress.repetitions or 0) + 1


def undo_rating(progress: UserCardProgress, old_interval: float, old_due_at, old_status: CardStatus) -> None:
    progress.interval_days = old_interval
    progress.due_at = old_due_at
    progress.status = old_status
