import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CardStatus(str, enum.Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    REVIEW = "REVIEW"
    MASTERED = "MASTERED"
    SUSPENDED = "SUSPENDED"


class Rating(str, enum.Enum):
    AGAIN = "AGAIN"
    HARD = "HARD"
    GOOD = "GOOD"
    EASY = "EASY"


class UserCardProgress(Base):
    __tablename__ = "user_card_progress"
    __table_args__ = (UniqueConstraint("user_id", "card_id", name="uq_user_card"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    status: Mapped[CardStatus] = mapped_column(Enum(CardStatus), default=CardStatus.NEW)
    interval_days: Mapped[float] = mapped_column(Float, default=0)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_rating: Mapped[Rating | None] = mapped_column(Enum(Rating), nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    card = relationship("Card", back_populates="progress_records")
