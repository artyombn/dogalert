import logging

from pydantic import ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_user_data import TelegramUser
from src.schemas.user import UserCreate
from src.services.user_service import UserServices

templates = Jinja2Templates(directory="src/fastapi/templates")
router = APIRouter(
    prefix="/registration",
    tags=["Registration"],
)

logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse, include_in_schema=True)
async def show_registration_page(
        request: Request,
        initData: str | None = None,
) -> HTMLResponse:
    user = TelegramUser.from_init_data(initData)
    if initData and user:
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "telegram_id": user.id,
            "initData": initData,
        })
    else:
        return templates.TemplateResponse("no_telegram_login.html", {
            "request": request,
        })

@router.post("/2", response_class=HTMLResponse, include_in_schema=True)
async def registration_step2(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: str = Form(...),
        region: str = Form(...),
        initData: str | None = None,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    try:
        tg_user_data = TelegramUser.from_init_data(initData)
        if not initData or not tg_user_data:
            return templates.TemplateResponse("no_telegram_login.html", {"request": request})

        logger.info(f"--- USER_FROM_TG = {tg_user_data}")
        logger.info(f"--- USER_FROM_FORM = {first_name}, {last_name}, {phone}, {region}")

        check_user_db = await UserServices.find_one_or_none_by_tgid(tg_user_data.id, session)
        if check_user_db:
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        new_user = UserCreate(
            username=tg_user_data.username,
            first_name=first_name,
            last_name=last_name,
            phone=PhoneNumber(phone),
            region=region,
            agreement=True,
        )
        logger.info(f"NEW_USER = {new_user}")

        try:
            user_created = await UserServices.create_user(
                user_data=new_user,
                session=session,
                telegram_id=tg_user_data.id,
            )
        except Exception as e:
            logger.error(f"User creation error = {e}")
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        if not user_created:
            logger.error("User creation failed: user_created is None")
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        response = templates.TemplateResponse("registration_done.html", {
            "request": request,
            "telegram_id": tg_user_data.id,
        })
        response.set_cookie(
            key="user_id",
            value=str(user_created.id),
            httponly=True,
            secure=True,
            max_age=3600 * 24 * 1,
        )
        logger.info("COOKIE REGISTER SET")
        return response

    except ValidationError as e:
        errors = e.errors()
        return templates.TemplateResponse("registration.html", {
            "request": request,
            "errors": errors,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "region": region,
            "initData": initData,
        })



