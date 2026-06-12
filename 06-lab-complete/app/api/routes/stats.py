from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.stats import DailyStats, DeckStats, StatsOverview
from app.services.stats_service import get_daily_stats, get_deck_stats, get_overview

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
def stats_overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_overview(db, user)


@router.get("/daily", response_model=list[DailyStats])
def stats_daily(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_daily_stats(db, user.id, days)


@router.get("/decks/{deck_id}", response_model=DeckStats)
def stats_deck(deck_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    result = get_deck_stats(db, user.id, deck_id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ")
    return result


@router.get("/review-history")
def review_history(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_daily_stats(db, user.id, days)
