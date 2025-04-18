from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from pydantic_extra_types.phone_numbers import PhoneNumber

    from .pet import Pet
    from .report import Report

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=15,
        description="Username must be between 3 and 15 symbols",
    )
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=15,
        description="First name must be between 2 and 15 symbols",
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=15,
        description="Last name must be between 2 and 15 symbols",
    )
    phone: PhoneNumber | None = Field(
        default=None,
        description="Phone number must be in international format",
    )
    region: str | None = Field(
        default=None,
        description="User region",
    )
    geo_latitude: float | None = Field(
        default=None,
        description="Latitude of user location",
    )
    geo_longitude: float | None = Field(
        default=None,
        description="Longitude of user location",
    )
    agreement: bool = Field(
        default=False,
        description="User agreement status",
    )

class UserCreate(UserBase):
    """Schema for creating a new user
    """

class UserUpdate(UserBase):
    """Schema for updating user
    """


class User(UserBase):
    """The main User schema for getting user data
    """

    id: int = Field(description="Unique user ID")
    telegram_id: int = Field(description="Unique telegram ID")
    created_at: datetime = Field(description="User creation timestamp")
    updated_at: datetime = Field(description="User last update timestamp")
    is_superuser: bool = Field(default=False, description="Superuser status")
    pets: list[Pet] = Field(
        default_factory=list,
        description="User's pets",
    )
    reports: list[Report] = Field(
        default_factory=list,
        description="User's reports",
    )

    class Config:
        """To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True
