from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from geoalchemy2.types import WKBElement
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.database.models.geo import GeoFilterType
from src.schemas.report import ReportBasePhoto as ReportBasePhoto_schema

if TYPE_CHECKING:
    from .user import User


class GeolocationBase(BaseModel):
    region: str = Field(
        min_length=3,
        max_length=30,
        description="Region name",
    )
    home_location: Annotated[str, WKBElement] = Field(
        description="Geography POINT object",
    )
    radius: int = Field(description="Geolocation radius")
    polygon: Annotated[str, WKBElement] = Field(
        description="Geography POLYGON object",
    )

    @field_validator("home_location")
    def validate_wkbelement_point(cls, value: str) -> str:
        if not value.startswith("POINT("):
            raise ValueError("Geography object home_location must be a valid WKT POINT string")
        return value

    @field_validator("polygon")
    def validate_wkbelement_polygon(cls, value: str) -> str:
        if not value.startswith("POLYGON("):
            raise ValueError("Geography object polygon must be a valid WKT POLYGON string")
        return value


class GeolocationCreate(GeolocationBase):
    """
    Schema for creating geolocation
    """

class GeolocationUpdate(BaseModel):
    """
    Schema for updating geolocation
    """

    region: str | None = Field(
        default="Moscow",
        min_length=3,
        max_length=30,
        description="Region name",
    )
    home_location: str | None = Field(
        default=None,
        description="Geography POINT string",
    )
    filter_type: GeoFilterType | None = Field(
        default=GeoFilterType.RADIUS,
        description="Chosen filter type for searching",
    )

    @field_validator("home_location")
    def validate_wkbelement_point(cls, value: str) -> str:
        if not value.startswith("POINT("):
            raise ValueError("Geography object home_location must be a valid WKT POINT string")
        return value

class Geolocation(GeolocationBase):
    id: int = Field(description="Geography ID")
    filter_type: GeoFilterType = Field(description="Chosen filter type for searching")

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class Coordinates(BaseModel):
    lat: float = Field(description="Geography latitude")
    lon: float = Field(description="Geography longitude")

class GeolocationNearest(BaseModel):
    home_location: Annotated[str, WKBElement] = Field(
        description="Geography POINT object",
    )
    radius: int = Field(description="Geography radius")

class GeolocationNearestWithRegion(BaseModel):
    home_location: Annotated[str, WKBElement] = Field(
        description="Geography POINT object",
    )
    radius: int = Field(description="Geography radius")
    region: str = Field(description="Geo User's city")

class GeolocationNearestResponse(GeolocationNearest):
    user: User = Field(description="Geography User")
    region: str = Field(description="Geography region")
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class GeolocationNearestResponseWithReports(GeolocationNearest):
    filter_type: str = Field(description="Geography filter type")
    region: str = Field(description="Geography region")
    distance: float = Field(description="Distance between 2 geographies")
    user: User = Field(description="Geography User")
    reports: list[ReportBasePhoto_schema] = Field(description="Nearest User's reports")
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

