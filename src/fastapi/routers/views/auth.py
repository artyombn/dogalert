import logging
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from src.database.db_session import get_async_session
from src.fastapi.dependencies.telegram_user_data import TelegramUser
from src.services.user_service import UserServices

templates = Jinja2Templates(directory="src/fastapi/templates")
router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/auth")
async def user_auth(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> RedirectResponse:
    data = await request.json()
    init_data = data.get("initData")

    logger.info(f"Received initData: {init_data}")

    if not init_data:
        logger.warning("initData not found. Redirecting to no_telegram_login.")
        return RedirectResponse(url="/no_telegram_login", status_code=303)

    telegram_user = TelegramUser.from_init_data(init_data)
    if telegram_user:
        user_db = await UserServices.find_one_or_none_by_tgid(telegram_user.id, session)
    else:
        logger.warning("telegram_user not found. Redirecting to no_telegram_login.")
        return RedirectResponse(url="/no_telegram_login", status_code=303)

    if not user_db:
        logger.info(f"INIT_DATA AUTH = {init_data}")
        response = RedirectResponse(
            url=f"/agreement?{urlencode({'initData': init_data})}",
            status_code=303,
        )
        return response

    response = RedirectResponse(url="/profile", status_code=303)
    response.set_cookie(
        key="user_id",
        value=str(user_db.id),
        httponly=True,
        secure=True,
        max_age=3600 * 24 * 1,
    )
    return response

@router.get("/no_telegram_login")
async def no_telegram_login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("no_telegram_login.html", {"request": request})


