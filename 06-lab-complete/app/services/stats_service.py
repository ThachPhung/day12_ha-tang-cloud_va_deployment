from datetime import datetime, timedelta, timezone

from sqlalchemy import func

from app.core.datetime_utils import ensure_utc, utc_now
from sqlalchemy.orm import Session

from app.models.card import Card
from app.models.deck import Deck
from app.models.progress import CardStatus, UserCardProgress
from app.models.review_log import ReviewLog
from app.models.user import User


def get_overview(db: Session, user: User) -> dict:
    now = utc_now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    progress_q = db.query(UserCardProgress).filter(UserCardProgress.user_id == user.id)

    due_candidates = progress_q.filter(
        UserCardProgress.status != CardStatus.NEW,
        UserCardProgress.status != CardStatus.SUSPENDED,
        UserCardProgress.due_at.isnot(None),
    ).all()
    due_today = sum(1 for p in due_candidates if ensure_utc(p.due_at) <= now)

    new_available = progress_q.filter(UserCardProgress.status == CardStatus.NEW).count()
    total_studied = progress_q.filter(UserCardProgress.status != CardStatus.NEW).count()
    mastered = progress_q.filter(UserCardProgress.status == CardStatus.MASTERED).count()
    streak = _calculate_streak(db, user.id)

    recent_decks = (
        db.query(Deck)
        .filter(Deck.owner_id == user.id, Deck.is_deleted == False)
        .order_by(Deck.updated_at.desc())
        .limit(5)
        .all()
    )

    return {
        "due_today": due_today,
        "new_available": new_available,
        "total_studied": total_studied,
        "mastered": mastered,
        "streak_days": streak,
        "recent_decks": [
            {"id": d.id, "name": d.name, "updated_at": d.updated_at.isoformat()}
            for d in recent_decks
        ],
    }


def _calculate_streak(db: Session, user_id: int) -> int:
    today = datetime.now(timezone.utc).date()
    streak = 0
    current = today
    while True:
        day_start = datetime.combine(current, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        count = (
            db.query(ReviewLog)
            .filter(
                ReviewLog.user_id == user_id,
                ReviewLog.is_undone == False,
                ReviewLog.reviewed_at >= day_start,
                ReviewLog.reviewed_at < day_end,
            )
            .count()
        )
        if count > 0:
            streak += 1
            current -= timedelta(days=1)
        else:
            break
    return streak


def get_daily_stats(db: Session, user_id: int, days: int = 30) -> list[dict]:
    results = []
    today = datetime.now(timezone.utc).date()
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        logs = (
            db.query(ReviewLog)
            .filter(
                ReviewLog.user_id == user_id,
                ReviewLog.is_undone == False,
                ReviewLog.reviewed_at >= day_start,
                ReviewLog.reviewed_at < day_end,
            )
            .all()
        )
        reviews = len(logs)
        good_easy = sum(1 for l in logs if l.rating.value in ("GOOD", "EASY"))
        results.append({
            "date": day.isoformat(),
            "reviews": reviews,
            "new_cards": sum(1 for l in logs if l.old_interval == 0),
            "good_easy_rate": round(good_easy / reviews * 100, 1) if reviews else 0,
        })
    return results


def get_deck_stats(db: Session, user_id: int, deck_id: int) -> dict | None:
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck:
        return None

    now = utc_now()
    cards = db.query(Card).filter(Card.deck_id == deck_id, Card.is_deleted == False).all()
    card_ids = [c.id for c in cards]

    progress_list = (
        db.query(UserCardProgress)
        .filter(UserCardProgress.user_id == user_id, UserCardProgress.card_id.in_(card_ids))
        .all()
    ) if card_ids else []

    progress_map = {p.card_id: p for p in progress_list}
    counts = {"NEW": 0, "LEARNING": 0, "REVIEW": 0, "MASTERED": 0, "SUSPENDED": 0, "due": 0}

    for card in cards:
        p = progress_map.get(card.id)
        status = p.status.value if p else "NEW"
        counts[status] = counts.get(status, 0) + 1
        if p and p.due_at and ensure_utc(p.due_at) <= now and status not in ("NEW", "SUSPENDED"):
            counts["due"] += 1

    return {
        "deck_id": deck.id,
        "deck_name": deck.name,
        "total_cards": len(cards),
        "new_count": counts.get("NEW", 0),
        "learning_count": counts.get("LEARNING", 0),
        "review_count": counts.get("REVIEW", 0),
        "mastered_count": counts.get("MASTERED", 0),
        "suspended_count": counts.get("SUSPENDED", 0),
        "due_count": counts["due"],
    }
