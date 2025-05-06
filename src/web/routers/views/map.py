import logging

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.map import Map, MapCreate
from src.services.map_service import MapServices

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/map",
    tags=["Map"],
)

@router.get("/", response_class=HTMLResponse)
async def map_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("map/index.html", {"request": request})

@router.get("/{id}", response_model=Map)
async def get_geometry(
        id: int,
        session: AsyncSession = Depends(get_async_session)
) -> Map:
    geometry = await MapServices.get_lake(id, session)
    if geometry is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return geometry

@router.post("/create", response_model=Map)
async def create_geometry(
        map_data: MapCreate,
        session: AsyncSession = Depends(get_async_session)
) -> Map:
    logger.debug(f"Creating lake with data: {map_data}")
    new_geometry = await MapServices.create_lake(
        map_data,
        session,
    )
    if new_geometry is None:
        raise HTTPException(status_code=404, detail="Map not found")
    return new_geometry


