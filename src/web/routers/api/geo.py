import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.database.models.geo import GeoFilterType
from src.schemas.geo import Coordinates, GeolocationNearest
from src.schemas.geo import Geolocation as Geolocation_schema
from src.services.geo_service import GeoServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/geo",
    tags=["API Geo"],
)

@router.post("/radius/tg_uids",
             summary="Get nearest Users' Telegram IDs by radius",
             response_model=dict,
             )
async def get_nearest_users_tguids_by_radius(
        geo_data: GeolocationNearest,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    nearest_users_tguids = await GeoServices.find_all_telegram_uids_within_radius(
        geo_data=geo_data,
        session=session,
    )
    logger.info(f"NEAR USERS TG LIST = {nearest_users_tguids}")
    return {"total": len(nearest_users_tguids), "nearest_users_tguids": nearest_users_tguids}

@router.post("/city/tg_uids",
             summary="Get nearest Users' Telegram IDs by city",
             response_model=dict,
             )
async def get_nearest_users_tguids_by_city(
        coords: Coordinates,
        city: str,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    geo_pydantic = Geolocation_schema(
        id=1,
        filter_type=GeoFilterType.REGION,
        region=city,
        home_location=f"POINT({coords.lon} {coords.lat})",
        radius=5000,
        polygon="POLYGON((30.5 50.45, 30.6 50.5, 30.55 50.55, 30.5 50.45))",
    )

    nearest_users_tguids = await GeoServices.find_all_telegram_uids_by_city(
        geo_data=geo_pydantic,
        session=session,
    )
    logger.info(f"NEAR USERS TG LIST = {nearest_users_tguids}")
    return {"total": len(nearest_users_tguids), "nearest_users_tguids": nearest_users_tguids}


@router.post("/radius", summary="Get nearest Users by radius", response_model=dict)
async def get_nearest_users_geos_by_radius(
        geo_data: GeolocationNearest,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    nearest_users = await GeoServices.find_all_geos_within_radius(
        geo_data=geo_data,
        session=session,
    )
    logger.info(f"NEAR_USERS = {nearest_users}")
    return {"total": len(nearest_users), "nearest_users": nearest_users}
