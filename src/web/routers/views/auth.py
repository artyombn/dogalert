import json
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.services.user_service import UserServices
from src.web.dependencies.telegram_user_data import TelegramUser

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter()

logger = logging.getLogger(__name__)

@router.post("/auth")
async def user_auth(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    data = await request.json()
    init_data = data.get("initData")

    logger.info(f"Received initData: {init_data}")

    if not init_data:
        logger.warning("initData not found. Returning JSON redirect.")
        return JSONResponse(
            status_code=200,
            content={"redirect_url": "/no_telegram_login"},
        )

    telegram_user = TelegramUser.from_init_data(init_data)
    if not telegram_user:
        logger.warning("telegram_user not found. Returning JSON redirect.")
        return JSONResponse(
            status_code=200,
            content={"redirect_url": "/no_telegram_login"},
        )

    user_db = await UserServices.find_one_or_none_by_tgid(telegram_user.id, session)
    if not user_db:
        logger.info(f"INIT_DATA AUTH = {init_data}")
        return JSONResponse(
            status_code = 200,
            content={"redirect_url": f"/agreement?{urlencode({'initData': init_data})}"},
    )

    response = JSONResponse(
        status_code = 200,
        content={"redirect_url": "/profile"},
    )

    cookie_data = json.dumps({"user_id": str(user_db.id), "photo_url": telegram_user.photo_url})
    response.set_cookie(
        key="user_data",
        value=cookie_data,
        httponly=True,
        secure=True,
        max_age=3600 * 24 * 1,
    )
    logger.info(f"COOKIE SET = {cookie_data}")
    return response

@router.get("/no_telegram_login")
async def no_telegram_login(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("no_telegram_login.html", {"request": request})


