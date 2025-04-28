import hashlib
import hmac
import json
import logging
import urllib
from urllib.parse import parse_qs, parse_qsl, unquote

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Body, Depends, HTTPException, status
from src.config.config import settings
from src.database.db_session import get_async_session
from src.schemas import User as User_schema
from src.schemas.telegram import InitDataRequest
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

"""
initDATA["user"]

{
  "id": 123456789,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "language_code": "en",
  "is_premium": true,
  "allows_write_to_pm": true
}

"""


def verify_telegram_auth(init_data: str) -> dict | None:
    if not settings.TOKEN:
        logger.error("Bot token is empty or not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bot token is not configured",
        )

    parsed_data = dict(parse_qsl(init_data))
    received_hash = parsed_data.get("hash")

    if not received_hash:
        logger.error("Hash is missing in init_data")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hash is missing in initData",
        )

    data_pairs = [
        (k, unquote(v)) for k, v in [pair.split("=", 1) for pair in init_data.split("&")]
        if k != "hash"
    ]
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_pairs))

    secret_key = hmac.new(b"WebAppData", settings.TOKEN.encode(), hashlib.sha256).digest()

    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if hmac.compare_digest(calculated_hash, received_hash):
        logger.info("Hashes match successfully!")
        return parsed_data

    logger.error("Hashes do not match")
    return None

async def get_current_user(
        init_data_body: InitDataRequest | None = Body(None),
        session: AsyncSession = Depends(get_async_session),
) -> User_schema | None:
    if init_data_body:
        init_data = init_data_body.initData
    else:
        raise HTTPException(status_code=400, detail="initData is required")

    init_data_decoded = urllib.parse.unquote(init_data)
    logger.debug(f"Decoded initData: {init_data_decoded}")

    parsed_data = verify_telegram_auth(init_data_decoded)

    if not parsed_data:
        return None

    try:
        user_json = parsed_data.get("user")
        if not isinstance(user_json, str):
            return None
        user_data = json.loads(user_json)
        telegram_id = user_data["id"]
    except Exception:
        return None

    user = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
    if user is None:
        return None
    return User_schema.model_validate(user)

def get_tg_id_from_initdata(init_data: str | None) -> int | None:
    if not init_data:
        return None
    parsed = parse_qs(init_data)
    user_str_list = parsed.get("user")
    if not user_str_list:
        return None
    try:
        user = json.loads(user_str_list[0])
        return user.get("id")
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


