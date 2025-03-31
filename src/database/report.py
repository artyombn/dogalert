from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from base_model import Base
from datetime import datetime
from enum import Enum


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
    title: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default=ReportStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # Location fields
    location: Mapped[str] = mapped_column(nullable=True)
    region: Mapped[str] = mapped_column(nullable=True, index=True)
    search_radius: Mapped[int] = mapped_column(default=5000)

    # Relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped["User"] = relationship(
        back_populates="reports",
    )
    pet_id: Mapped[int] = mapped_column(
        ForeignKey("pets.id"),
        nullable=False,
        index=True,
    )
    pet: Mapped["Pet"] = relationship(
        back_populates="reports",
    )
    photos: Mapped[List["ReportPhoto"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )

