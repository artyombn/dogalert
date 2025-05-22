import asyncio
import logging
import traceback

from aiogram.exceptions import TelegramRetryAfter
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from src.bot.create_bot import bot

log = logging.getLogger(__name__)

semaphore = asyncio.Semaphore(5)

async def send_notification_to_user(
        telegram_id: int,
        message: str,
        url: str,
):
    async with semaphore:
        while True:
            try:
                markup = None
                if url:
                    markup = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="🔎 Посмотреть объявление",
                            web_app=WebAppInfo(url=url),
                        )]
                    ])

                await bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    reply_markup=markup
                )
                await asyncio.sleep(0.3)
                break
            except TelegramRetryAfter as e:
                log.warning(f"Flood limit exceeded, sleeping for {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
            except TelegramAPIError as e:
                log.error(f"Telegram API error for user ({telegram_id}): {e}")
                break
            except Exception as e:
                log.error(f"Unexpected error for user ({telegram_id}): {e}\n{traceback.format_exc()}")
                break

