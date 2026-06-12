import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DeckVisibility(str, enum.Enum):
    private = "private"
    shared = "shared"


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    front_language: Mapped[str] = mapped_column(String(20), default="English")
    back_language: Mapped[str] = mapped_column(String(20), default="Vietnamese")
    visibility: Mapped[DeckVisibility] = mapped_column(
        Enum(DeckVisibility), default=DeckVisibility.private
    )
    new_cards_per_day: Mapped[int] = mapped_column(Integer, default=20)
    review_limit_per_day: Mapped[int] = mapped_column(Integer, default=100)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner = relationship("User", back_populates="decks")
    cards = relationship("Card", back_populates="deck")
