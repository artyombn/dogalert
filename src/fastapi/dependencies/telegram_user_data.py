from __future__ import annotations

import json
import logging

from pydantic import BaseModel

from src.fastapi.dependencies.telegram_auth import verify_telegram_auth

logger = logging.getLogger(__name__)

"""
initData:
query_id=...
&user={
        "id":...,
        "first_name":...,
        "last_name":...,
        "username":...,
        "language_code":...,
        "is_premium":...,
        "allows_write_to_pm":...,
        "photo_url":...
        }
&auth_date=...
&signature=...
"""

class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None

    class Config:
        extra = "ignore"

    @classmethod
    def from_init_data(cls, init_data: str | None) \
            -> TelegramUser | None:
        if not init_data:
            return None
        try:
            parsed_data = verify_telegram_auth(init_data)
            if not parsed_data:
                raise ValueError("Invalid signature")

            user_json = parsed_data.get("user")
            if not user_json:
                raise ValueError("No user data in initData")

            user_dict = json.loads(user_json)
            return cls(**user_dict)
        except ValueError as e:
            logger.error(f"Failed to process init_data: {str(e)}")
            return None
