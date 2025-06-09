import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter

from src.config.config import settings

log = logging.getLogger(__name__)

async def send_reminder_async(telegram_id: int, message: str) -> bool:
    celery_bot = Bot(token=settings.TOKEN)
    max_retries = 3
    try:
        for attempt in range(max_retries):
            try:
                await celery_bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                )
                log.info(f"Finish sending reminder to user {telegram_id}")
                return True

            except TelegramRetryAfter as e:
                log.warning(f"Flood limit exceeded, sleeping for {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)
                continue

            except TelegramAPIError as e:
                log.error(f"Telegram API error for user {telegram_id}: {e}")
                return False

            except Exception as e:
                log.error(
                    f"Unexpected error for user {telegram_id} (attempt {attempt + 1}): {e}",
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
        log.error(
            f"Failed to send message to user {telegram_id} after {max_retries} attempts",
        )
        return False

    finally:
        await celery_bot.session.close()


def send_reminder_sync(telegram_id: int, message: str) -> bool:
    log.info(f"Sending message to user {telegram_id}")

    try:
        return asyncio.run(send_reminder_async(telegram_id, message))
    except Exception as e:
        log.error(f"Error sending message to user {telegram_id}: {e}")
        return False
