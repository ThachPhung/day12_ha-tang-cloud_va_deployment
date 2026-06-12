from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.datetime_utils import ensure_utc, utc_now
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.card import Card
from app.models.deck import Deck, DeckVisibility
from app.models.progress import CardStatus, UserCardProgress
from app.models.user import User, UserRole
from app.schemas.deck import DeckCreate, DeckResponse, DeckUpdate

router = APIRouter(prefix="/decks", tags=["decks"])


def _deck_to_response(
    db: Session, deck: Deck, user: User, progress_user_id: int | None = None
) -> DeckResponse:
    now = utc_now()
    target_user_id = progress_user_id if progress_user_id is not None else user.id
    cards = db.query(Card).filter(Card.deck_id == deck.id, Card.is_deleted == False).all()
    card_ids = [c.id for c in cards]
    progress_list = (
        db.query(UserCardProgress)
        .filter(UserCardProgress.user_id == target_user_id, UserCardProgress.card_id.in_(card_ids))
        .all()
    ) if card_ids else []
    progress_map = {p.card_id: p for p in progress_list}

    due_count = 0
    new_count = 0
    studied = 0
    for card in cards:
        p = progress_map.get(card.id)
        status = p.status if p else CardStatus.NEW
        if status == CardStatus.NEW:
            new_count += 1
        elif status != CardStatus.SUSPENDED and p and p.due_at and ensure_utc(p.due_at) <= now:
            due_count += 1
        if p and status != CardStatus.NEW:
            studied += 1

    progress_percent = (studied / len(cards) * 100) if cards else 0
    owner = db.query(User).filter(User.id == deck.owner_id).first()

    return DeckResponse(
        id=deck.id,
        owner_id=deck.owner_id,
        owner_name=owner.display_name if owner else "",
        name=deck.name,
        description=deck.description,
        front_language=deck.front_language,
        back_language=deck.back_language,
        visibility=deck.visibility.value,
        new_cards_per_day=deck.new_cards_per_day,
        review_limit_per_day=deck.review_limit_per_day,
        card_count=len(cards),
        due_count=due_count,
        new_count=new_count,
        progress_percent=round(progress_percent, 1),
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


def _can_access(deck: Deck, user: User) -> bool:
    if user.role == UserRole.admin:
        return True
    if deck.owner_id == user.id:
        return True
    return deck.visibility == DeckVisibility.shared


def _can_edit(deck: Deck, user: User) -> bool:
    return deck.owner_id == user.id or user.role == UserRole.admin


@router.get("", response_model=list[DeckResponse])
def list_decks(
    search: str | None = Query(None),
    filter_type: str | None = Query(None),
    owner_id: int | None = Query(None),
    for_user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Deck).filter(Deck.is_deleted == False)
    progress_uid = for_user_id if for_user_id and user.role == UserRole.admin else None

    if user.role == UserRole.admin:
        if owner_id is not None:
            q = q.filter(Deck.owner_id == owner_id)
    else:
        q = q.filter(
            or_(Deck.owner_id == user.id, Deck.visibility == DeckVisibility.shared)
        )
        if owner_id is not None:
            raise HTTPException(status_code=403, detail="Không có quyền")

    if filter_type == "mine":
        q = q.filter(Deck.owner_id == user.id)
    elif filter_type == "shared":
        q = q.filter(Deck.visibility == DeckVisibility.shared, Deck.owner_id != user.id)
    if search:
        q = q.filter(Deck.name.ilike(f"%{search}%"))
    decks = q.order_by(Deck.updated_at.desc()).all()
    return [_deck_to_response(db, d, user, progress_uid) for d in decks]


@router.post("", response_model=DeckResponse, status_code=201)
def create_deck(data: DeckCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    owner_id = user.id
    if data.owner_id is not None:
        if user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Chỉ Admin được tạo bộ từ cho thành viên khác")
        target = db.query(User).filter(User.id == data.owner_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy thành viên")
        owner_id = data.owner_id

    deck = Deck(
        owner_id=owner_id,
        name=data.name.strip(),
        description=data.description,
        front_language=data.front_language,
        back_language=data.back_language,
        visibility=DeckVisibility(data.visibility),
        new_cards_per_day=data.new_cards_per_day,
        review_limit_per_day=data.review_limit_per_day,
    )
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return _deck_to_response(db, deck, user)


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(
    deck_id: int,
    for_user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck or not _can_access(deck, user):
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ")
    progress_uid = for_user_id if for_user_id and user.role == UserRole.admin else None
    return _deck_to_response(db, deck, user, progress_uid)


@router.patch("/{deck_id}", response_model=DeckResponse)
def update_deck(
    deck_id: int,
    data: DeckUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ")
    if not _can_edit(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền sửa bộ từ này")

    if data.name is not None:
        deck.name = data.name.strip()
    if data.description is not None:
        deck.description = data.description
    if data.visibility is not None:
        deck.visibility = DeckVisibility(data.visibility)
    if data.new_cards_per_day is not None:
        deck.new_cards_per_day = data.new_cards_per_day
    if data.review_limit_per_day is not None:
        deck.review_limit_per_day = data.review_limit_per_day
    deck.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(deck)
    return _deck_to_response(db, deck, user)


@router.delete("/{deck_id}")
def delete_deck(deck_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ")
    if not _can_edit(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền xóa bộ từ này")
    deck.is_deleted = True
    deck.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Đã xóa bộ từ"}
