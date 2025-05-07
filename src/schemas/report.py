from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.database.models.report import ReportStatus


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

class ReportPhotoBase(BaseModel):
    url: str = Field(description="Url report photo")


class ReportPhoto(ReportPhotoBase):
    """
    The main Report Photo schema for getting  photo data
    """

    id: int = Field(description="Unique report photo ID")
    report_id: int = Field(description="Report ID this photo belongs to")

    class Config:
        """
        To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True


class ReportPhotoCreate(ReportPhotoBase):
    """
    Schema for new Report Photo
    """


class ReportCreate(ReportBase):
    """
    Schema for creating a new Report
    """

class ReportUpdate(BaseModel):
    """
    Schema for updating Report
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

class Report(ReportBase):
    """
    The main Pet schema for getting pet data
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
        """
        To convert SQLAlchemy model into Pydantic
        """

        from_attributes = True


class ReportPhotoUpdate(BaseModel):
    """
    Schema for updating Report Photo
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
