import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/fastapi/templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/profile", response_model=None, include_in_schema=True)
async def show_profile_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = request.cookies.get("user_id")
    logger.info(f"PROFILE COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets = await UserServices.get_all_user_pets(user_db.id, session)
    reports = await UserServices.get_all_user_reports(user_db.id, session)

    return templates.TemplateResponse("menu/profile.html", {
        "request": request,
        "user": user_db,
        "pets": pets,
        "reports": reports,
    })

@router.get("/reports", response_class=HTMLResponse, include_in_schema=True)
async def show_reports_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = request.cookies.get("user_id")
    logger.info(f"REPORTS COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    reports = await ReportServices.get_all_reports(session)
    return templates.TemplateResponse("menu/reports.html", {
        "request": request,
        "reports": reports,
    })

@router.get("/health", response_class=HTMLResponse, include_in_schema=True)
async def show_health_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = request.cookies.get("user_id")
    logger.info(f"HEALTH COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("menu/health.html", {
        "request": request,
    })

@router.get("/reminders", response_class=HTMLResponse, include_in_schema=True)
async def show_reminders_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = request.cookies.get("user_id")
    logger.info(f"REMINDERS COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("menu/reminders.html", {
        "request": request,
    })
