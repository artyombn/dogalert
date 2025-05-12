import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.pet import Pet as Pet_schema
from src.schemas.pet import PetFirstPhotoResponse
from src.schemas.report import Report as Report_schema
from src.schemas.report import ReportFirstPhotoResponse
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.get_data_from_cookie import (
    get_user_id_from_cookie,
    get_user_photo_url_from_cookie,
)

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
    user_photo_url_str = get_user_photo_url_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user_db_task = UserServices.find_one_or_none_by_user_id(user_id, session)
    pets_task = UserServices.get_all_user_pets(user_id, session)
    reports_task = UserServices.get_all_user_reports(user_id, session)
    geo_task = UserServices.get_user_geolocation(user_id, session)

    user_db, pets, reports, geo = await asyncio.gather(
        user_db_task,
        pets_task,
        reports_task,
        geo_task,
    )

    if user_db is None or pets is None or reports is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets_with_first_photo = [
        PetFirstPhotoResponse(
            pet=Pet_schema.model_validate(pet),
            first_photo_url=pet.photos[0].url if pet.photos else None,
        )
        for pet in pets
    ]

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

    user_db_task = UserServices.find_one_or_none_by_user_id(user_id, session)
    reports_task = UserServices.get_all_user_reports(user_id, session)
    user_geo_task = UserServices.get_user_geolocation(user_id, session)

    user_db, reports, user_geo = await asyncio.gather(
        user_db_task,
        reports_task,
        user_geo_task,
    )

    if not reports:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    reports_with_first_photo = [
        ReportFirstPhotoResponse(
            report=Report_schema.model_validate(report),
            first_photo_url=report.photos[0].url if report.photos else None,
        )
        for report in reports
    ]

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("menu/reports.html", {
        "request": request,
        "user": user_db,
        "user_geo": user_geo,
        "reports_with_first_photo": reports_with_first_photo,
    })

@router.get("/health", response_class=HTMLResponse, include_in_schema=True)
async def show_health_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user_db_task = UserServices.find_one_or_none_by_user_id(user_id, session)
    pets_tasks = UserServices.get_all_user_pets(user_id, session)
    user_db, pets = await asyncio.gather(user_db_task, pets_tasks)

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    formatted_pets = []
    if pets:
        for pet in pets:
            formatted_pets.append({
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
