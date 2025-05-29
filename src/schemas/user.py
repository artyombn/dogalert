from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic_extra_types.phone_numbers import PhoneNumber

if TYPE_CHECKING:
    from .pet import Pet
    from .report import Report

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=25,
        description="Username must be between 3 and 25 symbols",
    )
    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
        description="First name must be between 2 and 20 symbols",
    )
    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
        description="Last name must be between 2 and 20 symbols",
    )
    phone: PhoneNumber | None = Field(
        default=None,
        description="Phone number must be in international format",
    )
    agreement: bool = Field(
        default=False,
        description="User agreement status",
    )

class UserCreate(UserBase):
    """
    Schema for creating a new user
    """

    telegram_photo: str | None = Field(
        default=None,
        description="User telegram photo url",
    )

class UserUpdate(UserBase):
    """
    Schema for updating user
    """


class User(UserBase):
    """
    The main User schema for getting user data
    """

    id: int = Field(description="Unique user ID")
    telegram_id: int = Field(description="Unique telegram ID")
    created_at: datetime = Field(description="User creation timestamp")
    updated_at: datetime = Field(description="User last update timestamp")
    is_superuser: bool = Field(default=False, description="Superuser status")


    class Config:
        """
        To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True

class UserPet(BaseModel):
    """
    Schema to convert SQLAlchemy model into Pydantic
    """

    pets: list[Pet] = Field(
        default_factory=list,
        description="User's pets",
    )

class UserReport(BaseModel):
    """
    Schema to convert SQLAlchemy model into Pydantic
    """

    reports: list[Report] = Field(
        default_factory=list,
        description="User's reports",
    )


class UserListResponse(BaseModel):
    total_users: int
    users: list[User]

class UserPetsResponse(BaseModel):
    total_pets: int
    pets: list[Pet] = Field(
        default_factory=list,
        description="User's pets",
    )

class UserReportsResponse(BaseModel):
    total_reports: int
    reports: list[Report] = Field(
        default_factory=list,
        description="User's reports",
    )

