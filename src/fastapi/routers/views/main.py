from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_auth import get_current_user
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

@router.get("/profile", response_class=HTMLResponse, include_in_schema=True)
async def show_profile_page(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id = 2
    user_db = await UserServices.find_one_or_none_by_user_id(user_id, session)
    pets = await UserServices.get_all_user_pets(user_id, session)
    reports = await UserServices.get_all_user_reports(user_id, session)
    return templates.TemplateResponse("profile.html", {
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
    reports = await ReportServices.get_all_reports(session)
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "reports": reports,
    })

@router.get("/agreement", response_class=HTMLResponse, include_in_schema=True)
async def show_agreement_page(
        request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("agreement.html", {
        "request": request,
    })

@router.post("/check_user")
async def check_user(
        current_user: User_schema = Depends(get_current_user),
) -> dict:
    return {"exists": True, "user": current_user}
