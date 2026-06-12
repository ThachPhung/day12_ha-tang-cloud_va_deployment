from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.card import Card
from app.models.deck import Deck, DeckVisibility
from app.models.progress import CardStatus, UserCardProgress
from app.models.user import User, UserRole
from app.schemas.card import CardCreate, CardResponse, CardUpdate, ImportPreviewResponse
from app.services.import_service import import_cards, parse_csv_content, validate_import_rows

router = APIRouter(tags=["cards"])


def _can_access_deck(deck: Deck, user: User) -> bool:
    if user.role == UserRole.admin:
        return True
    return deck.owner_id == user.id or deck.visibility == DeckVisibility.shared


def _can_edit_deck(deck: Deck, user: User) -> bool:
    return deck.owner_id == user.id or user.role == UserRole.admin


def _card_to_response(db: Session, card: Card, progress_user_id: int) -> CardResponse:
    progress = (
        db.query(UserCardProgress)
        .filter(UserCardProgress.user_id == progress_user_id, UserCardProgress.card_id == card.id)
        .first()
    )
    return CardResponse(
        id=card.id,
        deck_id=card.deck_id,
        front=card.front,
        back=card.back,
        phonetic=card.phonetic,
        part_of_speech=card.part_of_speech,
        example=card.example,
        example_translation=card.example_translation,
        notes=card.notes,
        tags=card.tags,
        image_url=card.image_url,
        audio_url=card.audio_url,
        status=progress.status.value if progress else "NEW",
        due_at=progress.due_at if progress else None,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
def list_cards(
    deck_id: int,
    search: str | None = Query(None),
    status_filter: str | None = Query(None),
    for_user_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck or not _can_access_deck(deck, user):
        raise HTTPException(status_code=404, detail="Không tìm thấy bộ từ")

    progress_user_id = user.id
    if for_user_id is not None:
        if user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Không có quyền")
        progress_user_id = for_user_id

    q = db.query(Card).filter(Card.deck_id == deck_id, Card.is_deleted == False)
    if search:
        q = q.filter(
            or_(
                Card.front.ilike(f"%{search}%"),
                Card.back.ilike(f"%{search}%"),
                Card.tags.ilike(f"%{search}%"),
            )
        )
    cards = q.order_by(Card.created_at.desc()).all()
    results = [_card_to_response(db, c, progress_user_id) for c in cards]

    if status_filter:
        results = [r for r in results if r.status == status_filter]

    return results


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=201)
def create_card(
    deck_id: int,
    data: CardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck or not _can_edit_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền thêm thẻ")

    duplicate = (
        db.query(Card)
        .filter(Card.deck_id == deck_id, Card.front.ilike(data.front), Card.is_deleted == False)
        .first()
    )
    if duplicate and not data.allow_duplicate:
        raise HTTPException(status_code=409, detail="Từ đã tồn tại trong bộ từ", headers={"X-Duplicate": "true"})

    card = Card(
        deck_id=deck_id,
        front=data.front,
        back=data.back,
        phonetic=data.phonetic,
        part_of_speech=data.part_of_speech,
        example=data.example,
        example_translation=data.example_translation,
        notes=data.notes,
        tags=data.tags,
        image_url=data.image_url,
        audio_url=data.audio_url,
    )
    db.add(card)
    deck.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(card)
    return _card_to_response(db, card, user.id)


@router.get("/cards/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.is_deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ")
    deck = db.query(Deck).filter(Deck.id == card.deck_id).first()
    if not deck or not _can_access_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền xem thẻ")
    return _card_to_response(db, card, user.id)


@router.patch("/cards/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    data: CardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    card = db.query(Card).filter(Card.id == card_id, Card.is_deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ")
    deck = db.query(Deck).filter(Deck.id == card.deck_id).first()
    if not deck or not _can_edit_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền sửa thẻ")

    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None and field in ("front", "back"):
            value = value.strip()
        setattr(card, field, value)
    card.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(card)
    return _card_to_response(db, card, user.id)


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.is_deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ")
    deck = db.query(Deck).filter(Deck.id == card.deck_id).first()
    if not deck or not _can_edit_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền xóa thẻ")
    card.is_deleted = True
    card.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Đã xóa thẻ"}


@router.post("/decks/{deck_id}/import/preview", response_model=ImportPreviewResponse)
async def import_preview(
    deck_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck or not _can_edit_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền import")

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .csv")

    content = (await file.read()).decode("utf-8-sig")
    _, rows, error = parse_csv_content(content)
    if error:
        raise HTTPException(status_code=400, detail=error)

    validated = validate_import_rows(db, deck_id, rows)
    return ImportPreviewResponse(
        valid_count=sum(1 for r in validated if r["is_valid"] and not r["is_duplicate"]),
        invalid_count=sum(1 for r in validated if not r["is_valid"]),
        duplicate_count=sum(1 for r in validated if r["is_duplicate"] and r["is_valid"]),
        rows=validated,
    )


@router.post("/decks/{deck_id}/import")
async def import_confirm(
    deck_id: int,
    file: UploadFile = File(...),
    skip_duplicates: bool = True,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    deck = db.query(Deck).filter(Deck.id == deck_id, Deck.is_deleted == False).first()
    if not deck or not _can_edit_deck(deck, user):
        raise HTTPException(status_code=403, detail="Không có quyền import")

    content = (await file.read()).decode("utf-8-sig")
    _, rows, error = parse_csv_content(content)
    if error:
        raise HTTPException(status_code=400, detail=error)

    validated = validate_import_rows(db, deck_id, rows)
    count = import_cards(db, deck_id, validated, skip_duplicates=skip_duplicates)
    deck.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"imported": count, "message": f"Đã import {count} thẻ"}
