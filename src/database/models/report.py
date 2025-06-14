from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:  # Only for mypy
    from src.database.models import Notification, Pet, User

class ReportStatus(str, Enum):
    ACTIVE = "active"
    FOUND = "found"
    CANCELLED = "cancelled"


class ReportPhoto(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(nullable=False)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    report: Mapped["Report"] = relationship(back_populates="photos")


class Report(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(nullable=False, index=True)
    content: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default=ReportStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user: Mapped["User | None"] = relationship(
        back_populates="reports",
    )
    pet_id: Mapped[int | None] = mapped_column(
        ForeignKey("pets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pet: Mapped["Pet | None"] = relationship(
        back_populates="reports",
    )
    photos: Mapped[list["ReportPhoto"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )

    notification: Mapped[list["Notification"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

