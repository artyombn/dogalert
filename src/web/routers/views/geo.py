import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.geo import Geolocation, GeolocationCreate
from src.services.geo_service import GeoServices

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/geo",
    tags=["Geolocation"],
)

@router.get("/", response_class=HTMLResponse)
async def map_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("map/index.html", {"request": request})

@router.get("/{id}", response_model=Geolocation)
async def get_geolocation(
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> Geolocation:
    geolocation = await GeoServices.get_geolocation(id, session)
    if geolocation is None:
        raise HTTPException(status_code=404, detail="Geolocation not found")
    return geolocation

@router.post("/create", response_model=Geolocation)
async def create_geolocation(
        user_id: int,
        geo_data: GeolocationCreate,
        session: AsyncSession = Depends(get_async_session),
) -> Geolocation:
    logger.debug(f"Creating geolocation with data: {geo_data}")
    new_geolocation = await GeoServices.create_geolocation(
        user_id,
        geo_data,
        session,
    )
    if new_geolocation is None:
        raise HTTPException(status_code=404, detail="Geolocation not found")
    return new_geolocation



