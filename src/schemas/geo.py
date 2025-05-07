from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated

from src.database.models.geo import GeoFilterType


class GeolocationBase(BaseModel):
    region: str = Field(
        min_length=3,
        max_length=30,
        description="Region name",
    )
    home_location: Annotated[str, WKBElement] = Field(
        description="Geometry POINT object",
    )
    radius: int = Field(description="Geolocation radius")
    polygon: Annotated[str, WKBElement] = Field(
        description="Geometry POLYGON object",
    )

    @field_validator("home_location")
    def validate_wkbelement_point(cls, value: str) -> str:
        if not value.startswith("POINT("):
            raise ValueError("Geom object home_location must be a valid WKT POINT string")
        return value

    @field_validator("polygon")
    def validate_wkbelement_polygon(cls, value: str) -> str:
        if not value.startswith("POLYGON("):
            raise ValueError("Geom object polygon must be a valid WKT POLYGON string")
        return value


class GeolocationCreate(GeolocationBase):
    """
    Schema for creating geolocation
    """

class Geolocation(GeolocationBase):
    id: int = Field(description="Geometry ID")
    filter_type: GeoFilterType = Field(description="Chosen filter type for searching")

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


