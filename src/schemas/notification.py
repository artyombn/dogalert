from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class NotificationMethod(str, Enum):
    TELEGRAM_CHAT = "telegram_chat"
    TELEGRAM_WEB = "telegram_web"
    EMAIL = "email"
    PHONE = "phone"


class NotificationBase(BaseModel):
    method: NotificationMethod = Field(
        default=NotificationMethod.TELEGRAM_CHAT,
        description="Send notification methods",
    )
    message: str = Field(
        min_length=10,
        max_length=400,
        description="Message must be between 10 and 400 symbols",
    )


class NotificationCreate(NotificationBase):
    """
    Schema for creating a new Notification
    """

    recipient_ids: list[int] = Field(description="Notification recipients IDs")
    sender_id: int = Field(description="Notification sender ID")
    report_id: int = Field(description="Notification report ID")


class Notification(NotificationBase):
    """
    The main Notification schema for getting/showing data
    """

    id: int = Field(description="Notification unique ID")
    created_at: datetime = Field(description="Notification creation timestamp")
    updated_at: datetime = Field(description="Notification update timestamp")
    recipient_ids: list[int] = Field(description="Notification recipients IDs")
    sender_id: int = Field(description="Notification sender ID")
    report_id: int = Field(description="Notification report ID")
