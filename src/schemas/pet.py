from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

# from pydantic_extra_types.color import Color

if TYPE_CHECKING:
    from .user import User
    from .report import Report

from pydantic import BaseModel, Field


class PetBase(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=15,
        description="Pet name must be between 2 and 15 symbols",
    )
    breed: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
        description="Pet breed must be between 2 and 30 symbols",
    )
    age: int | None = Field(
        default=None,
        ge=0,
        le=30,
        description="Pet age must be between 0 and 30 years",
    )
    color: str | None = Field(
        default=None,
        description="Chose the correct color of your pet",
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=200,
        description="Description must be between 10 and 200 symbols",
    )
    last_vaccination: datetime | None = Field(
        default=None,
        description="Use the correct date of last vaccination",
    )
    next_vaccination: datetime | None = Field(
        default=None,
        description="Use the correct date of next vaccination",
    )
    last_parasite_treatment: datetime | None = Field(
        default=None,
        description="Use the correct date of last parasite treatment",
    )
    next_parasite_treatment: datetime | None = Field(
        default=None,
        description="Use the correct date of next parasite treatment",
    )
    last_fleas_ticks_treatment: datetime | None = Field(
        default=None,
        description="Use the correct date of last fleas ticks treatment",
    )
    next_fleas_ticks_treatment: datetime | None = Field(
        default=None,
        description="Use the correct date of next fleas ticks treatment",
    )


class PetPhotoBase(BaseModel):
    url: str = Field(description="Pet Photo URL")

class PetPhotoCreate(PetPhotoBase):
    """Schema for new Pet Photo
    """

class PetCreate(PetBase):
    """Schema for creating a new Pet
    """

class PetUpdate(BaseModel):
    """Schema for updating Pet
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=15,
        description="Pet name must be between 2 and 15 symbols",
    )
    breed: str | None = Field(
        default=None,
        min_length=2,
        max_length=30,
        description="Pet breed must be between 2 and 30 symbols",
    )
    age: int | None = Field(
        default=None,
        ge=0,
        le=30,
        description="Pet age must be between 0 and 30 years",
    )
    color: str | None = Field(
        default=None,
        description="Color of the pet",
    )
    description: str | None = Field(
        default=None,
        min_length=10,
        max_length=200,
        description="Description must be between 10 and 200 symbols",
    )
    last_vaccination: datetime | None = Field(
        default=None,
        description="Date of last vaccination in ISO format (YYYY-MM-DD)",
    )
    next_vaccination: datetime | None = Field(
        default=None,
        description="Date of next vaccination in ISO format (YYYY-MM-DD)",
    )
    last_parasite_treatment: datetime | None = Field(
        default=None,
        description="Date of last parasite treatment in ISO format (YYYY-MM-DD)",
    )
    next_parasite_treatment: datetime | None = Field(
        default=None,
        description="Date of next parasite treatment in ISO format (YYYY-MM-DD)",
    )
    last_fleas_ticks_treatment: datetime | None = Field(
        default=None,
        description="Date of last fleas and ticks treatment in ISO format (YYYY-MM-DD)",
    )
    next_fleas_ticks_treatment: datetime | None = Field(
        default=None,
        description="Date of next fleas and ticks treatment in ISO format (YYYY-MM-DD)",
    )


class PetPhotoUpdate(BaseModel):
    """Schema for updating Pet Photo
    """

    id: int = Field(description="Pet Photo ID")
    url: str = Field(
        description="Pet Photo URL",
    )


class PetPhoto(PetPhotoBase):
    """The main Pet Photo schema for getting photo data
    """

    id: int = Field(description="Pet Photo ID")
    pet_id: int = Field(description="The ID of the pet this photo belongs to")

    class Config:
        """To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True

class Pet(PetBase):
    """The main Pet schema for getting pet data
    """

    id: int = Field(description="Unique pet ID")
    created_at: datetime = Field(description="Pet creation timestamp")
    updated_at: datetime = Field(description="Pet last update timestamp")

    class Config:
        """To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True

class PetOwners(BaseModel):
    """Schema to convert SQLAlchemy model into Pydantic
    """

    owners: list[User] = Field(
        default_factory=list,
        description="Pet's owners",
    )

class PetReports(BaseModel):
    """Schema to convert SQLAlchemy model into Pydantic
    """

    reports: list[Report] = Field(
        default_factory=list,
        description="Pet's reports",
    )

class PetListResponse(BaseModel):
    total_pets: int
    pets: list[Pet]

class PetOwnersResponse(BaseModel):
    total_owners: int
    owners: list[User] = Field(
        default_factory=list,
        description="List of pet owners",
    )

class PetReportsResponse(BaseModel):
    total_reports: int
    reports: list[Report] = Field(
        default_factory=list,
        description="List of pet reports",
    )

class PetPhotosResponse(BaseModel):
    total_photos: int
    photos: list[PetPhoto] = Field(
        default_factory=list,
        description="List of pet photos",
    )

