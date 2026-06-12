from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), index=True)
    front: Mapped[str] = mapped_column(String(255))
    back: Mapped[str] = mapped_column(Text)
    phonetic: Mapped[str | None] = mapped_column(String(100), nullable=True)
    part_of_speech: Mapped[str | None] = mapped_column(String(50), nullable=True)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_translation: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    deck = relationship("Deck", back_populates="cards")
    progress_records = relationship("UserCardProgress", back_populates="card")
