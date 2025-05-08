import logging

from fastapi import HTTPException
from geoalchemy2 import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import GeoLocation as GeoLocation_db
from src.schemas.geo import Geolocation as Geolocation_schema
from src.schemas.geo import GeolocationCreate

logger = logging.getLogger(__name__)


class GeoServices:
    @classmethod
    async def get_geolocation(
            cls,
            id: int,
            session: AsyncSession,
    ) -> Geolocation_schema | None:
        query = select(
            GeoLocation_db.id,
            GeoLocation_db.filter_type,
            GeoLocation_db.region,
            func.ST_AsText(GeoLocation_db.home_location).label("home_location"),
            GeoLocation_db.radius,
            func.ST_AsText(GeoLocation_db.polygon).label("polygon"),
            GeoLocation_db.use_current_location,
        ).filter_by(id=id)
        geo_result = await session.execute(query)
        row = geo_result.first()
        if row:
            return Geolocation_schema(**row._asdict())
        return None

    @classmethod
    async def create_geolocation(
            cls,
            user_id: int,
            geo_data: GeolocationCreate,
            session: AsyncSession,
    ) -> Geolocation_schema | None:
        data_dict = geo_data.model_dump(exclude_unset=True)

        separate_data = {
            "filter_type": data_dict.get("filter_type"),
            "region": data_dict.get("region"),
            "radius": data_dict.get("radius"),
            "use_current_location": data_dict.get("use_current_location"),
        }

        new_geo = GeoLocation_db(**separate_data)
        new_geo.user_id = user_id

        if isinstance(data_dict.get("home_location"), str):
            new_geo.home_location = WKTElement(data_dict.get("home_location"), srid=4326)  # type: ignore[assignment, arg-type]
        if isinstance(data_dict.get("polygon"), str):
            new_geo.polygon = WKTElement(data_dict.get("polygon"), srid=4326)  # type: ignore[assignment, arg-type]

        session.add(new_geo)
        try:
            await session.commit()
            await session.refresh(new_geo)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=422, detail=f"Failed to create Geolocation: {str(e)}")

        query = select(
            GeoLocation_db.id,
            GeoLocation_db.filter_type,
            GeoLocation_db.region,
            func.ST_AsText(GeoLocation_db.home_location).label("home_location"),
            GeoLocation_db.radius,
            func.ST_AsText(GeoLocation_db.polygon).label("polygon"),
            GeoLocation_db.use_current_location,
        ).filter_by(id=new_geo.id)

        result = await session.execute(query)
        row = result.first()

        if row:
            return Geolocation_schema(**row._asdict())
        return None
