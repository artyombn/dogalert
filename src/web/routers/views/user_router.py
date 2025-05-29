import asyncio
import logging

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.database.models.geo import GeoFilterType
from src.schemas.geo import Coordinates, GeolocationUpdate
from src.schemas.user import UserUpdate
from src.services.geo_service import GeoServices
from src.services.user_service import UserServices
from src.web.dependencies.city_geo_handles import check_city, extract_city_name, get_city_from_geo
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/profile/{id}", response_class=HTMLResponse, include_in_schema=True)
async def show_user_profile(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user = await UserServices.find_one_or_none_by_user_id(id, session)
    if user is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    user_photo_url_str = user.telegram_photo

    async with asyncio.TaskGroup() as tg:
        pets_task = tg.create_task(UserServices.get_all_user_pets(user.id, session))
        reports_task = tg.create_task(UserServices.get_all_user_reports(user.id, session))

    pets = pets_task.result()
    reports = reports_task.result()

    user_data_creation = format_russian_date(user.created_at)

    return templates.TemplateResponse("user/profile.html", {
        "request": request,
        "user_data_creation": user_data_creation,
        "user_photo": user_photo_url_str,
        "user": user,
        "pets": pets,
        "reports": reports,
    })

@router.get("/settings", response_class=HTMLResponse, include_in_schema=True)
async def show_user_settings_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if user_id_str is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_photo_url_str = user.telegram_photo

    user_geo = await UserServices.get_user_geolocation(user_id, session)
    if user_geo:
        user_coords = (user_geo.home_location[6:-1]).split(" ")

        aiohttp_session = request.app.state.aiohttp_session
        user_address_dict = await get_city_from_geo(
            lat=float(user_coords[1]),
            lon=float(user_coords[0]),
            session=aiohttp_session,
        )
    else:
        user_address_dict = None

    try:
        from phonenumbers import NumberParseException, PhoneNumberFormat, format_number, parse

        parsed = parse(str(user.phone), None)
        user_phone = format_number(parsed, PhoneNumberFormat.E164)
    except (NumberParseException, AttributeError):
        user_phone = ""

    return templates.TemplateResponse("user/settings.html", {
        "request": request,
        "user": user,
        "user_phone": user_phone,
        "user_photo_url": user_photo_url_str,
        "user_geo": user_geo,
        "user_address": user_address_dict["display_name"] or "не определен",  # type: ignore[index]
    })

@router.get("/all", response_class=HTMLResponse, include_in_schema=True)
async def show_users_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    users = await UserServices.get_all_users(session)
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
    })

@router.patch("/update/geo", response_model=None, include_in_schema=True)
async def update_user_geolocation(
        request: Request,
        coordinates: Coordinates,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    aiohttp_session = request.app.state.aiohttp_session

    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    user_id = int(user_id_str)
    logger.info(f"GOT USER ID = {user_id}")

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
    logger.info(f"USER GEO EXISTS = {user_geo_exists}")
    requested_user_city = requested_user_city_task.result()
    logger.info(f"REQUESTED USER CITY = {requested_user_city}")

    if not user_geo_exists:
        return JSONResponse(
            content={"status": "error", "message": "Геолокация не найдена"},
            status_code=404,
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
    try:
        geo_data = GeolocationUpdate(
            region=user_city or user_geo_exists.region,
            home_location=f"POINT({coordinates.lon} {coordinates.lat})",
            filter_type=user_geo_exists.filter_type,
        )
        logger.info(f"GEO DATA = {geo_data.__dict__}")
    except ValidationError as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка валидации. {e}"},
            status_code=500,
        )

    try:
        await GeoServices.update_geolocation(
            user_id=user_id,
            geo_data=geo_data,
            session=session,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка при обновлении {e}"},
            status_code=500,
        )
    return JSONResponse(
        content={
            "status": "success",
            "message": "Гео данные успешно обновлены",
        },
        status_code=200,
    )

@router.patch("/update/geo/filter_type", response_model=None, include_in_schema=True)
async def update_user_geo_filter_type(
        request: Request,
        filter_type: GeoFilterType,
        radius: int | None = Query(None),
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:

    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={
                "status": "error",
                "message": "Пользователь не найден",
            },
            status_code=404,
        )

    user_id = int(user_id_str)
    try:
        user_updated_geo = await GeoServices.update_geo_filter_type(
            user_id=user_id,
            filter_type=filter_type,
            radius=radius if radius is not None else None,
            session=session,
        )
        logger.info(f"USER UPDATED GEO = {user_updated_geo}")
        if not user_updated_geo:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "У пользователя отсутствует геолокация",
                },
                status_code=404,
            )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Ошибка при обновлении фильтра геолокации {e}"},
            status_code=404,
        )
    return JSONResponse(
        content={
            "status": "success",
            "updated_user_geo": user_updated_geo.__dict__,
        },
        status_code=200,
    )

@router.patch("/update", response_model=None, include_in_schema=True)
async def update_user_info(
        request: Request,
        first_name: str | None = Form(None, example=None),
        last_name: str | None = Form(None, example=None),
        phone: str | None = Form(None, example=None),
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={
                "status": "error",
                "message": "Пользователь не найден",
            },
            status_code=404,
        )

    user_id = int(user_id_str)
    user_exists = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user_exists is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )

    updated_user_schema = UserUpdate(
        first_name=first_name,
        last_name=last_name,
        phone=phone,  # type: ignore[arg-type]
    )
    try:
        await UserServices.update_user(
            user_id=user_id,
            user_data=updated_user_schema,
            session=session,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка при обновлении {e}"},
            status_code=500,
        )
    return JSONResponse(
        content={
            "status": "success",
            "message": "Данные успешно обновлены",
        },
        status_code=200,
    )
