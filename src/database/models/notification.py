from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from .base_model import Base

if TYPE_CHECKING:  # Only for mypy
    from src.database.models import Report, User

class Notification(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    method: Mapped[str | None] = mapped_column(nullable=True)
    message: Mapped[str | None] = mapped_column(nullable=True)

    # Recipient & Sender & Report
    recipient_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    sender: Mapped["User"] = relationship(
        back_populates="notification_sent",
        passive_deletes=True,
    )
    report: Mapped["Report"] = relationship(
        back_populates="notification",
        passive_deletes=True,
    )
