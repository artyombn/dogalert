import asyncio
import logging
import traceback

from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from src.bot.create_bot import bot
from src.celery_app.config import app

log = logging.getLogger(__name__)


async def send_reminder_async(telegram_id: int, message: str) -> None:
    log.info(f"Start sending reminder to user {telegram_id}")
    while True:
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
            )
            log.info(f"Finish sending reminder to user {telegram_id}")
            break
        except TelegramRetryAfter as e:
            log.warning(f"Flood limit exceeded, sleeping for {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
        except TelegramAPIError as e:
            log.error(f"Telegram API error for user ({telegram_id}): {e}")
            break
        except Exception as e:
            log.error(
                f"Unexpected error for user ({telegram_id}): "
                f"{e}\n{traceback.format_exc()}",
            )
            break


@app.task
def send_vaccination_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора делать вакцинацию питомцу {pet_name}!"
    for tg_id in telegram_ids:
        try:
            asyncio.run(send_reminder_async(tg_id, message))
        except Exception as e:
            log.error(f"Failed to send vaccination reminder - {tg_id}, {e}")


@app.task
def send_parasite_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора обработать от паразитов питомца {pet_name}!"
    for tg_id in telegram_ids:
        try:
            asyncio.run(send_reminder_async(tg_id, message))
        except Exception as e:
            log.error(f"Failed to send parasite reminder - {tg_id}, {e}")

@app.task
def send_fleas_ticks_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора сделать обработку от блох и клещей для питомца {pet_name}!"
    for tg_id in telegram_ids:
        try:
            asyncio.run(send_reminder_async(tg_id, message))
        except Exception as e:
            log.error(f"Failed to send parasite reminder - {tg_id}, {e}")
