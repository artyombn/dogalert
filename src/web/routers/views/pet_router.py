import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.services.pet_service import PetServices
from src.services.user_service import UserServices
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/pets",
    tags=["Pets"],
)

@router.get("/add_pet", response_class=HTMLResponse, include_in_schema=True)
async def add_new_pet(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("pet/new_pet.html", {
        "request": request,
        "user": user_db,
    })

@router.get("/profile", response_class=HTMLResponse, include_in_schema=True)
async def show_pet_profile(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pet = await PetServices.find_one_or_none_by_id(
        pet_id=id,
        session=session,
    )
    if pet is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    return templates.TemplateResponse("pet/profile.html", {
        "request": request,
        "pet": pet,
    })
