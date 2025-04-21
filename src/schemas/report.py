from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from src.database.models.report import ReportStatus

if TYPE_CHECKING:
    from src.schemas import Pet, User

from pydantic import BaseModel, Field


class ReportBase(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=50,
        description="Title must be between 3 and 50 symbols",
    )
    content: str = Field(
        min_length=10,
        max_length=400,
        description="Content must be between 10 and 400 symbols",
    )
    location: str | None = Field(
        default=None,
        description="Last location where pet has been lost",
    )
    region: str | None = Field(
        default=None,
        description="Region where pet has been lost",
    )


class ReportPhotoBase(BaseModel):
    url: str = Field(description="Url report photo")
    report_id: int | None = Field(
        default=None,
        description="Report ID this photo belongs to",
    )


class ReportPhoto(ReportPhotoBase):
    """The main Report Photo schema for getting  photo data
    """

    id: int = Field(description="Unique report photo ID")

    class Config:
        """To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True


class ReportPhotoCreate(ReportPhotoBase):
    """Schema for new Report Photo
    """


class ReportCreate(ReportBase):
    """Schema for creating a new Report
    """

class ReportUpdate(BaseModel):
    """Schema for updating Report
    """

    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Title must be between 3 and 50 symbols",
    )
    content: str | None = Field(
        default=None,
        min_length=10,
        max_length=400,
        description="Content must be between 10 and 400 symbols",
    )
    location: str | None = Field(
        default=None,
        description="Last location where pet has been lost",
    )
    region: str | None = Field(
        default=None,
        description="Region where pet has been lost",
    )


class Report(ReportBase):
    """The main Pet schema for getting pet data
    """

    id: int = Field(description="Unique report ID")
    status: ReportStatus = Field(
        default=ReportStatus.ACTIVE,
        description="Report status",
    )
    created_at: datetime = Field(description="Report creation timestamp")
    updated_at: datetime = Field(description="Report creation timestamp")
    user_id: int = Field(description="associated reporter's id")
    pet_id: int = Field(description="Associated pet id")

    class Config:
        """To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True


class ReportPhotoUpdate(BaseModel):
    """Schema for updating Report Photo
    """

    url: str | None = Field(
        default=None,
        description="Url report photo",
    )
    report_id: int = Field(description="Report ID this photo belongs to")


class ReportListResponse(BaseModel):
    total_reports: int
    reports: list[Report]

class ReportPhotosResponse(BaseModel):
    total_photos: int
    photos: list[ReportPhoto] = Field(
        default_factory=list,
        description="Report photos",
    )