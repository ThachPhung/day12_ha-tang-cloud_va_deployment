from sqlalchemy.orm import Session

from app.models.deck import Deck, DeckVisibility
from app.models.user import User
from app.services.stats_service import get_deck_stats, get_overview


def get_member_progress_report(db: Session, member_id: int) -> dict | None:
    user = db.query(User).filter(User.id == member_id).first()
    if not user:
        return None

    overview = get_overview(db, user)

    owned_decks = (
        db.query(Deck)
        .filter(Deck.owner_id == member_id, Deck.is_deleted == False)
        .order_by(Deck.updated_at.desc())
        .all()
    )
    shared_decks = (
        db.query(Deck)
        .filter(
            Deck.owner_id != member_id,
            Deck.visibility == DeckVisibility.shared,
            Deck.is_deleted == False,
        )
        .order_by(Deck.updated_at.desc())
        .all()
    )

    decks_data = []
    seen_ids: set[int] = set()
    for deck in owned_decks + shared_decks:
        if deck.id in seen_ids:
            continue
        seen_ids.add(deck.id)
        stats = get_deck_stats(db, member_id, deck.id)
        if not stats:
            continue
        owner = db.query(User).filter(User.id == deck.owner_id).first()
        total = stats["total_cards"]
        studied = total - stats["new_count"]
        decks_data.append({
            "deck_id": deck.id,
            "deck_name": deck.name,
            "owner_name": owner.display_name if owner else "",
            "visibility": deck.visibility.value,
            "total_cards": total,
            "new_count": stats["new_count"],
            "learning_count": stats["learning_count"],
            "review_count": stats["review_count"],
            "mastered_count": stats["mastered_count"],
            "due_count": stats["due_count"],
            "progress_percent": round(studied / total * 100, 1) if total else 0,
        })

    return {
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "due_today": overview["due_today"],
        "new_available": overview["new_available"],
        "total_studied": overview["total_studied"],
        "mastered": overview["mastered"],
        "streak_days": overview["streak_days"],
        "last_login_at": user.last_login_at,
        "decks": decks_data,
    }
