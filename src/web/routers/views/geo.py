import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.geo import Coordinates, Geolocation, GeolocationCreate
from src.services.geo_service import GeoServices
from src.services.user_service import UserServices
from src.web.dependencies.city_geo_handles import (
    check_city,
    extract_city_name,
    get_city_from_geo,
    get_geo_from_city,
)
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/geo",
    tags=["Geolocation"],
)

@router.get("/", response_class=HTMLResponse)
async def map_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("map/index.html", {"request": request})

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

@router.post("/get-location", response_model=dict)
async def get_user_location(
        coordinates: Coordinates,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse | None:
    aiohttp_session = request.app.state.aiohttp_session

    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )
    logger.info(f"Coordinates: lat = {coordinates.lat}, lon = {coordinates.lon}")

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_geo_exists_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))
        requested_user_city_task = tg.create_task(
            get_city_from_geo(
                lat=coordinates.lat,
                lon=coordinates.lon,
                session=aiohttp_session,
            ),
        )

    user_geo_exists = user_geo_exists_task.result()
    requested_user_city = requested_user_city_task.result()

    if user_geo_exists:
        return JSONResponse(
            content={"status": "error", "message": "Вы уже добавили домашнюю локацию"},
            status_code=400,
        )

    if not requested_user_city:
        return JSONResponse(
            content={"status": "error", "message": "Не удалось найти ваш город"},
            status_code=404,
        )

    if not check_city(requested_user_city):
        return JSONResponse(
            content={"status": "error", "message": "Город не найден в списке городов России"},
            status_code=404,
        )

    user_city = extract_city_name(requested_user_city)

    geo_data = GeolocationCreate(
        region=user_city or "Moscow",
        home_location=f"POINT({coordinates.lon} {coordinates.lat})",
        radius=50000,
        polygon="POLYGON((30.5 50.45, 30.6 50.5, 30.55 50.55, 30.5 50.45))",
    )
    logger.info(f"GEO_DATA = {geo_data}")

    await GeoServices.create_geolocation(
        user_id=user_id,
        geo_data=geo_data,
        session=session,
    )
    return JSONResponse(
        content={
            "status": "success",
            "redirect_url": "/registration/pet_question",
            "lat": coordinates.lat,
            "lon": coordinates.lon,
            "city": user_city,
        },
        status_code=200,
    )

@router.get("/get-city-coords", response_model=dict)
async def get_coords_by_city_name(
        city: str,
        request: Request,
) -> JSONResponse:
    aiohttp_session = request.app.state.aiohttp_session
    geo = await get_geo_from_city(city, aiohttp_session)
    logger.info(f"GEO = {geo}")
    if not geo:
        return JSONResponse(
            content={"status": "error", "message": "Город не найден. Проверьте название"},
            status_code=404,
        )
    return JSONResponse(
        content={"status": "success", "lat": geo["lat"], "lon": geo["lon"]},
        status_code=200,
    )

@router.get("/get-city-name", response_model=dict)
async def get_city_name_by_coords(
        lat: float,
        lon: float,
        request: Request,
) -> JSONResponse | None:

    aiohttp_session = request.app.state.aiohttp_session
    requested_city = await get_city_from_geo(
        lat=lat,
        lon=lon,
        session=aiohttp_session,
    )
    if requested_city is None:
        return JSONResponse(
            content={"status": "error", "message": "Не удалось найти ваш город"},
            status_code=404,
        )

    predicted_city = extract_city_name(requested_city)
    if predicted_city is None:
        return JSONResponse(
            content={"status": "error", "message": "Не удалось найти ваш город"},
            status_code=404,
        )

    if not check_city(requested_city):
        return JSONResponse(
            content={"status": "error", "message": "Город находится за пределами России"},
            status_code=400,
        )

    return JSONResponse(
        content={"status": "success", "city": predicted_city},
        status_code=200,
    )

@router.get("/{id}", response_model=Geolocation)
async def get_geolocation(
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> Geolocation:
    geolocation = await GeoServices.get_geolocation(id, session)
    if geolocation is None:
        raise HTTPException(status_code=404, detail="Geolocation not found")
    return geolocation
