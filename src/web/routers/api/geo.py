import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.geo import GeolocationNearest
from src.services.geo_service import GeoServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/geo",
    tags=["API Geo"],
)

@router.post("/radius", summary="Get nearest users by radius", response_model=dict)
async def get_nearest_users_geos_by_radius(
        geo_data: GeolocationNearest,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    nearest_users = await GeoServices.find_all_geos_within_radius(
        geo_data=geo_data,
        session=session,
    )
    logger.info(f"NEAR_USERS = {nearest_users}")
    return {"nearest_users": nearest_users}
