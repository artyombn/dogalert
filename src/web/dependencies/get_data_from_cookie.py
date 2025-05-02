import json
import logging

from fastapi import Request
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")

def get_user_id_from_cookie(request: Request) -> str | None:
    try:
        user_data_str = request.cookies.get("user_data")
        if not user_data_str:
            return None

        user_data = json.loads(user_data_str)
        return user_data.get("user_id")
    except (json.JSONDecodeError, KeyError):
        return None

def get_user_photo_url_from_cookie(request: Request) -> str | None:
    try:
        user_data_str = request.cookies.get("user_data")
        if not user_data_str:
            return None

        user_data = json.loads(user_data_str)
        return user_data.get("photo_url")
    except (json.JSONDecodeError, KeyError):
        return None
