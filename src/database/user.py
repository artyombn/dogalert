from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger
from typing import List
from base_model import Base
from datetime import datetime
from association_tables import user_pet_association

class User(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(nullable=True, index=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # Location fields
    region: Mapped[str] = mapped_column(nullable=True, index=True)
    geo_latitude: Mapped[float] = mapped_column(nullable=True)
    geo_longitude: Mapped[float] = mapped_column(nullable=True)

    # Management fields
    agreement: Mapped[bool] = mapped_column(default=False)
    is_superuser: Mapped[bool] = mapped_column(default=False)

    # Relationships
    pets: Mapped[List["Pet"]] = relationship(
        secondary=user_pet_association,
        back_populates="owners",
        cascade="all, delete",
    )
    reports: Mapped[List["Report"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
