import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
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

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets = await UserServices.get_all_user_pets(user_db.id, session)
    reports = await UserServices.get_all_user_reports(user_db.id, session)
    user_data_creation = format_russian_date(user_db.created_at)

    return templates.TemplateResponse("menu/profile.html", {
        "request": request,
        "user": user_db,
        "user_data_creation": user_data_creation,
        "user_photo": user_photo_url_str,
        "pets": pets,
        "reports": reports,
    })

@router.get("/reports", response_class=HTMLResponse, include_in_schema=True)
async def show_reports_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    reports = await UserServices.get_all_user_reports(user_db.id, session)
    return templates.TemplateResponse("menu/reports.html", {
        "request": request,
        "user": user_db,
        "reports": reports,
    })

@router.get("/health", response_class=HTMLResponse, include_in_schema=True)
async def show_health_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets = await UserServices.get_all_user_pets(user_db.id, session)
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

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("menu/reminders.html", {
        "request": request,
    })
