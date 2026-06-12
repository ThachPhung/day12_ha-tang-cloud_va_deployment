from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.session import SessionStatus, StudySession
from app.models.user import User
from app.schemas.study import AnswerRequest, AnswerResponse, SessionCreate, SessionFinishResponse, SessionResponse
from app.services.study_service import (
    answer_card,
    create_session,
    finish_session,
    get_session_next,
    suspend_card,
    undo_last_answer,
)

router = APIRouter(prefix="/study", tags=["study"])


def _card_dict(card, progress) -> dict:
    return {
        "id": card.id,
        "deck_id": card.deck_id,
        "front": card.front,
        "back": card.back,
        "phonetic": card.phonetic,
        "part_of_speech": card.part_of_speech,
        "example": card.example,
        "example_translation": card.example_translation,
        "notes": card.notes,
        "tags": card.tags,
        "image_url": card.image_url,
        "audio_url": card.audio_url,
        "status": progress.status.value,
        "is_new": progress.status.value == "NEW",
    }


def _get_session(db: Session, session_id: int, user: User) -> StudySession:
    session = db.query(StudySession).filter(StudySession.id == session_id).first()
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên học")
    return session


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def start_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = create_session(db, user, data.deck_id)
    next_item = get_session_next(db, session, user)
    current = _card_dict(next_item[0], next_item[1]) if next_item else None
    return SessionResponse(
        id=session.id,
        deck_id=session.deck_id,
        status=session.status.value,
        total_cards=session.total_cards,
        completed_cards=session.completed_cards,
        remaining_cards=max(0, session.total_cards - session.completed_cards),
        current_card=current,
    )


@router.get("/sessions/{session_id}/next-card", response_model=SessionResponse)
def next_card(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.active:
        raise HTTPException(status_code=400, detail="Phiên học đã kết thúc")

    next_item = get_session_next(db, session, user)
    current = _card_dict(next_item[0], next_item[1]) if next_item else None
    remaining = session.total_cards - session.completed_cards if not next_item else (
        session.total_cards - session.completed_cards
    )
    return SessionResponse(
        id=session.id,
        deck_id=session.deck_id,
        status=session.status.value,
        total_cards=session.total_cards,
        completed_cards=session.completed_cards,
        remaining_cards=remaining if next_item else 0,
        current_card=current,
    )


@router.post("/sessions/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: int,
    data: AnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session(db, session_id, user)
    if session.status != SessionStatus.active:
        raise HTTPException(status_code=400, detail="Phiên học đã kết thúc")
    if data.rating not in ("AGAIN", "HARD", "GOOD", "EASY"):
        raise HTTPException(status_code=400, detail="Đánh giá không hợp lệ")

    try:
        result = answer_card(db, session, user, data.card_id, data.rating, data.response_time_ms)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AnswerResponse(success=True, progress=result["progress"], session=result["session"])


@router.post("/sessions/{session_id}/undo")
def undo_answer(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session(db, session_id, user)
    if not undo_last_answer(db, session, user):
        raise HTTPException(status_code=400, detail="Không có câu trả lời để hoàn tác")
    return {"message": "Đã hoàn tác"}


@router.post("/sessions/{session_id}/finish", response_model=SessionFinishResponse)
def finish_study_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _get_session(db, session_id, user)
    result = finish_session(db, session)
    return SessionFinishResponse(**result)


@router.post("/cards/{card_id}/suspend")
def suspend_study_card(
    card_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    suspend_card(db, user.id, card_id)
    return {"message": "Đã tạm dừng thẻ"}
