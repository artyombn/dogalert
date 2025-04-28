from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_auth import get_current_user, get_tg_id_from_initdata
from src.schemas import User as User_schema
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

templates = Jinja2Templates(directory="src/fastapi/templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/users", response_class=HTMLResponse, include_in_schema=True)
async def show_users_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    users = await UserServices.get_all_users(session)
    return templates.TemplateResponse("users.html", {
        "request": request,
        "users": users,
    })

@router.get("/profile", response_model=None, include_in_schema=True)
async def show_profile_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
        initData: str | None = None,
) -> HTMLResponse:
    if not initData:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    telegram_id = get_tg_id_from_initdata(initData)
    if telegram_id is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pets = await UserServices.get_all_user_pets(user_db.id, session)
    reports = await UserServices.get_all_user_reports(user_db.id, session)

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user_db,
        "pets": pets,
        "reports": reports,
        "initData": initData,
    })

@router.get("/reports", response_class=HTMLResponse, include_in_schema=True)
async def show_reports_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    reports = await ReportServices.get_all_reports(session)
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "reports": reports,
    })

@router.get("/agreement", response_class=HTMLResponse, include_in_schema=True)
async def show_agreement_page(
        request: Request,
        initData: str | None = None,
) -> HTMLResponse:
    if initData:
        telegram_id = get_tg_id_from_initdata(initData)
        return templates.TemplateResponse("agreement.html", {
            "request": request,
            "telegram_id": telegram_id,
            "initData": initData,
        })
    else:
        return templates.TemplateResponse("no_telegram_login.html", {
            "request": request,
        })


@router.get("/registration", response_class=HTMLResponse, include_in_schema=True)
async def show_registration_page(
        request: Request,
        initData: str | None = None,
) -> HTMLResponse:
    if initData:
        telegram_id = get_tg_id_from_initdata(initData)
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "telegram_id": telegram_id,
            "initData": initData,
        })
    else:
        return templates.TemplateResponse("no_telegram_login.html", {
            "request": request,
        })

@router.post("/check_user")
async def check_user(
        current_user: User_schema = Depends(get_current_user),
) -> dict:
    if current_user:
        return {"exists": True, "user": current_user}
    return {"exists": False}
