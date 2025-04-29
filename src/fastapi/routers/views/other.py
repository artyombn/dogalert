import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_user_data import TelegramUser
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/fastapi/templates")
router = APIRouter()

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

@router.get("/agreement", response_class=HTMLResponse, include_in_schema=True)
async def show_agreement_page(
        request: Request,
        initData: str | None = None,
) -> HTMLResponse:

    logger.info(f"INIT_DATA AGREEMENT = {initData}")
    telegram_user = TelegramUser.from_init_data(initData)
    if initData and telegram_user:
        return templates.TemplateResponse("agreement.html", {
            "request": request,
            "telegram_id": telegram_user.id,
            "initData": initData,
        })
    else:
        return templates.TemplateResponse("no_telegram_login.html", {
            "request": request,
        })

@router.get("/error", response_class=HTMLResponse, include_in_schema=True)
async def show_error_page(
        request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("something_goes_wrong.html", {"request": request})


@router.post("/update_state")
async def update_user_state(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> dict:
    body = await request.json()
    init_data = body.get("initData")
    new_state = body.get("new_state")
    print({"init_data": init_data, "new_state": new_state})
    return {"init_data": init_data, "new_state": new_state}
