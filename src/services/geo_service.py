import logging

from fastapi import HTTPException
from geoalchemy2 import WKTElement, functions
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import GeoLocation as GeoLocation_db
from src.database.models import Report as Report_db
from src.database.models import ReportStatus
from src.database.models import User as User_db
from src.database.models.geo import GeoFilterType
from src.schemas import User as User_schema
from src.schemas.geo import Geolocation as Geolocation_schema
from src.schemas.geo import (
    GeolocationCreate,
    GeolocationNearest,
    GeolocationNearestResponse,
    GeolocationNearestResponseWithReports,
    GeolocationUpdate,
)
from src.schemas.report import ReportBasePhoto as ReportBasePhoto_schema

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
    async def update_and_get_geo(
            cls,
            geo: GeoLocation_db,
            session: AsyncSession,
    ) -> Geolocation_schema | None:
        try:
            await session.commit()
            await session.refresh(geo)
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
        ).filter_by(id=geo.id)

        result = await session.execute(query)
        row = result.first()

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
        return await cls.update_and_get_geo(new_geo, session)

    @classmethod
    async def update_geolocation(
            cls,
            user_id: int,
            geo_data: GeolocationUpdate,
            session: AsyncSession,
    ) -> Geolocation_schema | None:
        query = select(GeoLocation_db).filter_by(user_id=user_id)
        result = await session.execute(query)

        user_geo = result.scalar_one_or_none()
        if not user_geo:
            raise HTTPException(status_code=404, detail="Geolocation not found")

        try:
            user_geo.region = geo_data.region  # type: ignore[assignment]
            user_geo.home_location = WKTElement(geo_data.home_location, srid=4326)  # type: ignore[assignment, arg-type]
            user_geo.filter_type = geo_data.filter_type  # type: ignore[assignment]

            await session.commit()
            await session.refresh(user_geo)
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=422, detail=f"Failed to update Geolocation: {str(e)}")

        query_updated_geo = select(
            GeoLocation_db.id,
            GeoLocation_db.filter_type,
            GeoLocation_db.region,
            func.ST_AsText(GeoLocation_db.home_location).label("home_location"),
            GeoLocation_db.radius,
            func.ST_AsText(GeoLocation_db.polygon).label("polygon"),
            GeoLocation_db.use_current_location,
        ).filter_by(id=user_geo.id)

        result_updated_geo = await session.execute(query_updated_geo)
        row = result_updated_geo.first()

        if row:
            return Geolocation_schema(**row._asdict())
        return None

    @classmethod
    async def update_geo_filter_type(
            cls,
            user_id: int,
            filter_type: GeoFilterType,
            radius: int | None,
            session: AsyncSession,
    ) -> Geolocation_schema | None:
        query = select(GeoLocation_db).filter_by(user_id=user_id)
        result = await session.execute(query)
        user_geo = result.scalar_one_or_none()

        if not user_geo:
            return None

        user_geo.filter_type = filter_type
        user_geo.radius = radius or user_geo.radius
        return await cls.update_and_get_geo(user_geo, session)

    @classmethod
    async def find_all_geos_within_radius(
            cls,
            geo_data: GeolocationNearest,
            session: AsyncSession,
    ) -> list[GeolocationNearestResponse]:

        coords = geo_data.home_location[6:-1]
        lat = coords.split(" ")[1]
        lon = coords.split(" ")[0]

        user_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
        logger.info(f"USER_POINT = {user_point}")
        query = select(
            GeoLocation_db.user,
            GeoLocation_db.radius,
            GeoLocation_db.region,
            func.ST_AsText(GeoLocation_db.home_location).label("home_location"),
        ).where(
            functions.ST_DWithin(GeoLocation_db.home_location, user_point, geo_data.radius),
        )
        result = await session.execute(query)
        rows = result.all()
        logger.info(f"ROW NEAREST = {rows}")

        return [
            GeolocationNearestResponse(
                home_location=row.home_location,
                radius=row.radius,
                user=row.user,
                region=row.region,
            )
            for row in rows
        ]

    @classmethod
    async def find_all_geos_within_radius_with_user_reports(
            cls,
            geo_data: GeolocationNearest,
            session: AsyncSession,
    ) -> list[GeolocationNearestResponseWithReports]:

        coords = geo_data.home_location[6:-1]
        lat = coords.split(" ")[1]
        lon = coords.split(" ")[0]

        user_point = WKTElement(f"POINT({lon} {lat})", srid=4326)
        logger.info(f"USER_POINT = {user_point}")
        query = (
            select(
                GeoLocation_db,
                func.ST_AsText(GeoLocation_db.home_location).label("home_location"),
                functions.ST_Distance(
                    GeoLocation_db.home_location,
                    user_point,
                    use_spheroid=True,
                ).label("distance"),
            )
            .join(User_db, GeoLocation_db.user)
            .join(Report_db, Report_db.user_id == User_db.id)
            .where(
                functions.ST_DWithin(
                    GeoLocation_db.home_location,
                    user_point,
                    geo_data.radius,
                    use_spheroid=True,
                ),
                Report_db.status == ReportStatus.ACTIVE,
            )
            .options(
                selectinload(GeoLocation_db.user)
                .selectinload(User_db.reports)
                .selectinload(Report_db.photos),
            )
            .order_by("distance")
            .distinct()
        )
        result = await session.execute(query)
        rows_geos = result.all()
        logger.info(f"--- ROWS - GEOS = {rows_geos}")

        return [
            GeolocationNearestResponseWithReports(
                home_location=row[1],
                distance=row[2],
                radius=row[0].radius,
                filter_type=row[0].filter_type,
                region=row[0].region,
                user=User_schema.model_validate(row[0].user),
                reports=[
                    ReportBasePhoto_schema.model_validate(report)
                    for report in row[0].user.reports
                ],
            )
            for row in rows_geos
        ]

