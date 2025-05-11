from enum import Enum
from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:  # Only for mypy
    from src.database.models import User


class GeoFilterType(str, Enum):
    REGION = "region"
    RADIUS = "radius"
    POLYGON = "polygon"

class GeoLocation(Base):

    # Main fields
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filter_type: Mapped[GeoFilterType] = mapped_column(default=GeoFilterType.RADIUS)
    region: Mapped[str] = mapped_column(nullable=True, index=True)
    home_location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    radius: Mapped[int] = mapped_column(nullable=True)
    polygon: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POLYGON", srid=4326),
        nullable=True,
    )
    use_current_location: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    user: Mapped["User"] = relationship(
        back_populates="geolocation",
    )

