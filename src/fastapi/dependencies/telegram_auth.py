import hashlib
import hmac
import json
import logging
import urllib
from urllib.parse import parse_qsl, unquote

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status
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
        init_data_request: InitDataRequest,
        session: AsyncSession = Depends(get_async_session),
) -> User_schema:
    try:
        init_data_decoded = urllib.parse.unquote(init_data_request.initData)
        logger.debug(f"Decoded initData: {init_data_decoded}")

        parsed_data = verify_telegram_auth(init_data_decoded)

        if not parsed_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData")

        user_json = parsed_data.get("user")
        if not user_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing user data in initData",
            )

        user_data = json.loads(user_json)
        telegram_id = user_data.get("id")
        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram ID missing in user data",
            )

        user = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return User_schema.model_validate(user)

    except Exception as e:
        logger.error(f"Error processing initData: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid initData format",
        )


