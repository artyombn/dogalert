from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .association_tables import user_pet_association
from .base_model import Base

if TYPE_CHECKING:  # Only for mypy
    from src.database.models import GeoLocation, Notification, Pet, Report


class User(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Management fields
    agreement: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    state: Mapped[str] = mapped_column(nullable=True, default=None)

    # Relationships Pets & Reports & Geolocation
    pets: Mapped[list["Pet"]] = relationship(
        secondary=user_pet_association,
        back_populates="owners",
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    geolocation: Mapped["GeoLocation"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete",
    )

    # Notification relationships
    notification_sent: Mapped[list["Notification"]] = relationship(
        back_populates="sender",
        foreign_keys="[Notification.sender_id]",
        passive_deletes=True,
    )

