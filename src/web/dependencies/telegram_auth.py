import hashlib
import hmac
import logging
from urllib.parse import parse_qsl, unquote

from fastapi import HTTPException, status

from src.config.config import settings

logger = logging.getLogger(__name__)

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
