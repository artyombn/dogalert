import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.get_data_from_cookie import get_user_photo_url_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/profile", response_class=HTMLResponse, include_in_schema=True)
async def show_user_profile(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_photo_url_str = get_user_photo_url_from_cookie(request)

    user = await UserServices.find_one_or_none_by_user_id(id, session)
    if user is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    pets = await UserServices.get_all_user_pets(user.id, session)
    reports = await UserServices.get_all_user_reports(user.id, session)
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
) -> HTMLResponse:
    return templates.TemplateResponse("user/settings.html", {
        "request": request,
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
