import asyncio
import logging

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.database.models.geo import GeoFilterType
from src.schemas.geo import GeolocationNearest, GeolocationNearestWithRegion
from src.schemas.pet import Pet as Pet_schema
from src.schemas.pet import PetFirstPhotoResponse
from src.schemas.report import Report as Report_schema
from src.schemas.report import ReportFirstPhotoResponse
from src.services.geo_service import GeoServices
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.extract_nearest_report_data import extract_data
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/profile", response_model=None, include_in_schema=True)
async def show_profile_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        pets_task = tg.create_task(UserServices.get_all_user_pets(user_id, session))
        reports_task = tg.create_task(UserServices.get_all_user_reports(user_id, session))
        geo_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))

    user_db = user_db_task.result()
    pets = pets_task.result()
    reports = reports_task.result()
    geo = geo_task.result()

    if user_db is None or pets is None or reports is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets_with_first_photo = [
        PetFirstPhotoResponse(
            pet=Pet_schema.model_validate(pet),
            first_photo_url=pet.photos[0].url if pet.photos else None,
        )
        for pet in pets
    ]

    user_photo_url_str = user_db.telegram_photo
    user_data_creation = format_russian_date(user_db.created_at)

    return templates.TemplateResponse("menu/profile.html", {
        "request": request,
        "user": user_db,
        "user_data_creation": user_data_creation,
        "user_photo": user_photo_url_str,
        "reports": reports,
        "geo": geo.region if geo else None,
        "pets_with_first_photo": pets_with_first_photo,
    })

@router.get("/reports", response_class=HTMLResponse, include_in_schema=True)
async def show_reports_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        reports_task = tg.create_task(UserServices.get_all_user_reports(user_id, session))
        user_geo_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))

    user_db = user_db_task.result()
    reports = reports_task.result()
    user_geo = user_geo_task.result()

    if user_db is None or reports is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_reports = [
        ReportFirstPhotoResponse(
            report=Report_schema.model_validate(report),
            first_photo_url=report.photos[0].url if report.photos else None,
        )
        for report in reports
    ]

    return templates.TemplateResponse("menu/reports.html", {
        "request": request,
        "user": user_db,
        "user_geo": user_geo,
        "user_reports": user_reports,
    })

@router.get("/reports/nearby", response_class=JSONResponse)
async def get_nearby_reports(
            request: Request,
            filter_type: str = Query(..., description="Geo filter type: radius, region, polygon"),
            session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return JSONResponse(
            content={"error": "User not found"},
            status_code=401,
        )

    user_id = int(user_id_str)

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        user_geo_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))

    user_db = user_db_task.result()
    user_geo = user_geo_task.result()

    if user_db is None or user_geo is None:
        return JSONResponse(
            content={"error": "User not found"},
            status_code=404,
        )

    geo_data: GeolocationNearest | GeolocationNearestWithRegion  # mypy assignment

    if filter_type == GeoFilterType.RADIUS:
        geo_data = GeolocationNearest(
            home_location=user_geo.home_location,
            radius=user_geo.radius,
        )
        nearest_geo = await GeoServices.find_all_geos_within_radius_with_user_reports(
            geo_data=geo_data,
            session=session,
        )
        logger.info(
            f"NEAREST GEO BF ({len(nearest_geo)}) = "
            f"{[geo.__dict__ for geo in nearest_geo]}",
        )
    elif filter_type == GeoFilterType.REGION:
        geo_data = GeolocationNearestWithRegion(
            home_location=user_geo.home_location,
            radius=user_geo.radius,
            region=user_geo.region,
        )
        nearest_geo = await GeoServices.find_all_geos_by_city_with_user_reports(
            geo_data=geo_data,
            session=session,
        )
        logger.info(
            f"NEAREST GEO BF ({len(nearest_geo)}) = "
            f"{[geo.__dict__ for geo in nearest_geo]}",
        )
    elif filter_type == GeoFilterType.POLYGON:

        # THE SAME AS FOR GeoFilterType.RADIUS
        # WILL BE UPDATED LATER
        geo_data = GeolocationNearest(
            home_location=user_geo.home_location,
            radius=user_geo.radius,
        )
        nearest_geo = await GeoServices.find_all_geos_within_radius_with_user_reports(
            geo_data=geo_data,
            session=session,
        )
        logger.info(
            f"NEAREST GEO BF ({len(nearest_geo)}) = "
            f"{[geo.__dict__ for geo in nearest_geo]}",
        )
    else:
        return JSONResponse(
            content={"error": "Invalid filter type"},
            status_code=400,
        )

    if len(nearest_geo) >= 1:
        nearest_geo_dict = {geo.user.id: geo for geo in nearest_geo}
        user_to_remove = user_db.id

        if user_to_remove in nearest_geo_dict:
            del nearest_geo_dict[user_to_remove]

        nearest_geo_reports = list(nearest_geo_dict.values())
        logger.info(
            f"NEAREST GEO AFT ({len(nearest_geo_reports)}) = "
            f"{[geo.__dict__ for geo in nearest_geo]}",
        )

        """
         {
            "report_id": report_id,
            "report_title": report_title,
            "report_content": report_content,
            "report_status": report_status,
            "report_first_photo_url": report_first_photo_url,
            "report_region": report_region,
            "geo": geo,
            "geo_distance": geo_distance,
        }
        """

        nearest_reports_with_data = []
        for geo_schema in nearest_geo_reports:
            for report in geo_schema.reports:
                nearest_reports_with_data.append(extract_data(report, geo_schema))

    else:
        nearest_reports_with_data = []

    return JSONResponse(
        content={"reports": nearest_reports_with_data},
    )

@router.get("/health", response_class=HTMLResponse, include_in_schema=True)
async def show_health_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        pets_tasks = tg.create_task(UserServices.get_all_user_pets(user_id, session))

    user_db = user_db_task.result()
    pets = pets_tasks.result()

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    formatted_pets = []
    if pets:
        for pet in pets:
            formatted_pets.append({
                "id": pet.id,
                "name": pet.name,
                "breed": pet.breed,
                "age": pet.age,
                "color": pet.color,
                "description": pet.description,
                "last_vaccination": format_russian_date(pet.last_vaccination),
                "next_vaccination": format_russian_date(pet.next_vaccination),
                "last_parasite_treatment": format_russian_date(pet.last_parasite_treatment),
                "next_parasite_treatment": format_russian_date(pet.next_parasite_treatment),
                "last_fleas_ticks_treatment": format_russian_date(pet.last_fleas_ticks_treatment),
                "next_fleas_ticks_treatment": format_russian_date(pet.next_fleas_ticks_treatment),
            })
    return templates.TemplateResponse("menu/health.html", {
        "request": request,
        "pets": formatted_pets,
    })

@router.get("/reminders", response_class=HTMLResponse, include_in_schema=True)
async def show_reminders_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user_db = await UserServices.find_one_or_none_by_user_id(user_id, session)

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("menu/reminders.html", {
        "request": request,
    })

@router.get("/docs", response_class=HTMLResponse, response_model=None)
async def custom_swagger_ui(request: Request) -> Response:
    host = request.headers.get("host")
    if host != "api.dogalert.ru":
        return RedirectResponse(url="/")
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")
