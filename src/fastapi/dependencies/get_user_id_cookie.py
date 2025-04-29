import logging

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/fastapi/templates")

def get_user_id_from_cookie(request: Request) -> str | HTMLResponse:
    user_id_str = request.cookies.get("user_id")
    logger.info(f"PROFILE COOKIE = {user_id_str}")

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})
    return user_id_str
