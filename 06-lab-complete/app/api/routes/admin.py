from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_admin_user
from app.core.database import get_db
from app.models.deck import Deck
from app.models.user import User
from app.schemas.admin import MemberProgressReport
from app.schemas.deck import DeckResponse
from app.services.admin_service import get_member_progress_report

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/members/{user_id}/progress", response_model=MemberProgressReport)
def member_progress(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    report = get_member_progress_report(db, user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
    return report


@router.get("/members/{user_id}/decks", response_model=list[DeckResponse])
def member_decks(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    from app.api.routes.decks import _deck_to_response

    member = db.query(User).filter(User.id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")

    decks = (
        db.query(Deck)
        .filter(Deck.owner_id == user_id, Deck.is_deleted == False)
        .order_by(Deck.updated_at.desc())
        .all()
    )
    return [_deck_to_response(db, d, member) for d in decks]
