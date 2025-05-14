import json
import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.user import UserCreate
from src.services.user_service import UserServices
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie
from src.web.dependencies.telegram_user_data import TelegramUser

templates = Jinja2Templates(directory="src/web/templates")
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
    telegram_user = TelegramUser.from_init_data(initData)
    if initData and telegram_user:
        return templates.TemplateResponse("register/registration.html", {
            "request": request,
            "telegram_user": telegram_user,
            "initData": initData,
        })
    else:
        return templates.TemplateResponse("no_telegram_login.html", {
            "request": request,
        })

@router.post("/2", response_model=None, include_in_schema=True)
async def registration_step2(
        request: Request,
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: str = Form(...),
        initData: str | None = None,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    telegram_user = TelegramUser.from_init_data(initData)
    if not initData or not telegram_user:
        return JSONResponse(
            content={"status": "error", "message": "Ошибка Telegram авторизации"},
            status_code=400,
        )

    logger.info(f"--- USER_FROM_TG = {telegram_user}")
    logger.info(f"--- USER_FROM_FORM = {first_name}, {last_name}, {phone}")

    check_user_db = await UserServices.find_one_or_none_by_tgid(telegram_user.id, session)
    if check_user_db:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь уже зарегистрирован"},
            status_code=400,
        )

    try:
        new_user = UserCreate(
            username=telegram_user.username,
            first_name=first_name,
            last_name=last_name,
            phone=PhoneNumber(phone),
            agreement=True,
        )
        logger.info(f"NEW_USER = {new_user}")
    except Exception as e:
        logger.error(f"Phone number validation error = {e}")
        return JSONResponse(
            content={"status": "error", "message": "Неверный формат телефона"},
            status_code=500,
        )

    try:
        user_created = await UserServices.create_user(
            user_data=new_user,
            session=session,
            telegram_id=telegram_user.id,
        )
    except Exception as e:
        logger.error(f"User creation error = {e}")
        return JSONResponse(
            content={"status": "error", "message": "Ошибка при создании пользователя"},
            status_code=500,
        )

    if not user_created:
        logger.error("User creation failed: user_created is None")
        return JSONResponse(
            content={"status": "error", "message": "Создание пользователя не удалось"},
            status_code=500,
        )

    cookie_data = json.dumps(
        {
            "user_id": str(user_created.id),
            "photo_url": telegram_user.photo_url,
        },
    )

    response = JSONResponse(
        content={
            "status": "success",
            "redirect_url": "/registration/geolocation",
        },
        status_code=200,
    )
    response.set_cookie(
        key="user_data",
        value=cookie_data,
        httponly=True,
        secure=True,
        max_age=3600 * 24 * 1,
    )
    logger.info("COOKIE REGISTER SET")
    return response

@router.get("/geolocation", response_class=HTMLResponse, include_in_schema=True)
async def register_geolocation(
        request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("register/geolocation.html", {"request": request})

@router.get("/pet_question", response_class=HTMLResponse, include_in_schema=True)
async def pet_questions(
        request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("register/reg_pet_question.html", {"request": request})


@router.get("/registration_done", response_class=HTMLResponse, include_in_schema=True)
async def show_registration_done(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("register/registration_done.html", {
        "request": request,
        "user": user_db,
    })

