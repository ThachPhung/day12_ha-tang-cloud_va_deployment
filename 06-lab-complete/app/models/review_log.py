from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.progress import Rating


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int | None] = mapped_column(ForeignKey("study_sessions.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    rating: Mapped[Rating] = mapped_column(Enum(Rating))
    old_interval: Mapped[float] = mapped_column(Float, default=0)
    new_interval: Mapped[float] = mapped_column(Float, default=0)
    old_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    new_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    is_undone: Mapped[bool] = mapped_column(default=False)
    requeue_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
