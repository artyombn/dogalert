import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.user import UserUpdate
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.get_data_from_cookie import get_user_photo_url_from_cookie, get_user_id_from_cookie

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
    user_id = int(get_user_id_from_cookie(request))
    user_photo_url_str = get_user_photo_url_from_cookie(request)

    user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_geo = await UserServices.get_user_geolocation(user_id, session)

    try:
        from phonenumbers import parse, format_number, PhoneNumberFormat, NumberParseException

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

@router.put("/update/{user_id}", response_model=None, include_in_schema=True)
async def update_user_info(
        request: Request,
        user_id: int,
        first_name: str | None = Form(None, example=None),
        last_name: str | None = Form(None, example=None),
        phone: str | None = Form(None, example=None),
        session: AsyncSession = Depends(get_async_session)
) -> JSONResponse:

    user_exists = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user_exists is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )

    updated_user_schema = UserUpdate(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
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