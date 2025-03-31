from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from base_model import Base
from datetime import datetime
from association_tables import user_pet_association


class PetPhoto(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"))
    pet: Mapped["Pet"] = relationship(back_populates="photos")

class Pet(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    breed: Mapped[Optional[str]] = mapped_column(nullable=True)
    age: Mapped[Optional[int]] = mapped_column(nullable=True)
    color: Mapped[Optional[str]] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # Medicine info
    last_vaccination: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_vaccination: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_parasite_treatment: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_parasite_treatment: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    last_fleas_ticks_treatment: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_fleas_ticks_treatment: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    owners: Mapped[List["User"]] = relationship(
        secondary=user_pet_association,
        back_populates="pets",
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="pet",
    )
    photos: Mapped[List["PetPhoto"]] = relationship(
        back_populates="pet",
    )