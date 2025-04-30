import logging

from pydantic import ValidationError, BaseModel
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_user_data import TelegramUser
from src.schemas.pet import PetCreate
from src.schemas.user import UserCreate
from src.services.pet_service import PetServices
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
        telegram_user = TelegramUser.from_init_data(initData)
        if not initData or not telegram_user:
            return templates.TemplateResponse("no_telegram_login.html", {"request": request})

        logger.info(f"--- USER_FROM_TG = {telegram_user}")
        logger.info(f"--- USER_FROM_FORM = {first_name}, {last_name}, {phone}, {region}")

        check_user_db = await UserServices.find_one_or_none_by_tgid(telegram_user.id, session)
        if check_user_db:
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        new_user = UserCreate(
            username=telegram_user.username,
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
                telegram_id=telegram_user.id,
            )
        except Exception as e:
            logger.error(f"User creation error = {e}")
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        if not user_created:
            logger.error("User creation failed: user_created is None")
            return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

        response = templates.TemplateResponse("register/reg_pet_question.html", {
            "request": request
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
        return templates.TemplateResponse("register/registration.html", {
            "request": request,
            "errors": errors,
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "region": region,
            "initData": initData,
            "telegram_user": telegram_user,
        })

@router.get("/reg_pet", response_class=HTMLResponse, include_in_schema=True)
async def pet_registration(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
):
    user_id_str = request.cookies.get("user_id")
    logger.info(f"REG PET COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("register/reg_pet.html", {"request": request})


@router.get("/registration_done", response_class=HTMLResponse, include_in_schema=True)
async def show_registration_done(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
):
    user_id_str = request.cookies.get("user_id")
    logger.info(f"REG DONE COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("register/registration_done.html", {
        "request": request,
        "user": user_db,
    })

@router.post("/submit_pet_register", response_class=HTMLResponse, include_in_schema=True)
async def submit_pet_answers(
        request: Request,
        pet: PetCreate,
        session: AsyncSession = Depends(get_async_session),
):
    user_id_str = request.cookies.get("user_id")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    logger.info(f"PET DATA = {pet}")
    logger.info(f"USER_DB = {user_db} + his cookie id = {user_id_str}")

    pet_create = await PetServices.create_pet(
        owner_id=user_db.id,
        pet_data=pet,
        session=session
    )

    return RedirectResponse(url="/profile", status_code=303)
