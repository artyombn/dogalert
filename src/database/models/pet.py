from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .association_tables import user_pet_association
from .base_model import Base

if TYPE_CHECKING:  # Only for mypy
    from src.database.models import Report, User

class PetPhoto(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"))
    pet: Mapped["Pet"] = relationship(
        back_populates="photos",
        passive_deletes=True,
    )

class Pet(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, index=True)
    breed: Mapped[str | None] = mapped_column(nullable=True, index=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    color: Mapped[str | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Medicine info
    last_vaccination: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_vaccination: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_parasite_treatment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_parasite_treatment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_fleas_ticks_treatment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_fleas_ticks_treatment: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    owners: Mapped[list["User"]] = relationship(
        secondary=user_pet_association,
        back_populates="pets",
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="pet",
    )
    photos: Mapped[list["PetPhoto"]] = relationship(
        back_populates="pet",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
