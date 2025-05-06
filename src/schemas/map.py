from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_validator
from geoalchemy2.types import WKBElement
from typing_extensions import Annotated


class MapBase(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=25,
        description="Geometry name",
    )
    geom: Annotated[str, WKBElement] = Field(
        description="Geometry object",
    )

    @field_validator("geom")
    def validate_geom(cls, value):
        if not isinstance(value, str) or not value.startswith("POINT("):
            raise ValueError("geom must be a valid WKT POINT string")
        return value


class MapCreate(MapBase):
    """
    Create Map
    """

class Map(MapBase):
    id: int = Field(description="Geometry ID")
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

