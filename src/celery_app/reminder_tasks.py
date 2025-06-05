import logging

from src.celery_app.config import celery_app
from src.celery_app.separate_tg_bot import send_reminder_sync

log = logging.getLogger(__name__)


@celery_app.task
def send_vaccination_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора делать вакцинацию питомцу {pet_name}!"
    for tg_id in telegram_ids:
        try:
            success = send_reminder_sync(tg_id, message)
            if success:
                log.info(f"Vaccination reminder sent successfully to user: {tg_id}")
            else:
                log.error(f"Failed to send vaccination reminder to user {tg_id}")
        except Exception as e:
            log.error(f"Failed to send vaccination reminder - {tg_id}, {e}")


@celery_app.task
def send_parasite_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора обработать от паразитов питомца {pet_name}!"
    for tg_id in telegram_ids:
        try:
            success = send_reminder_sync(tg_id, message)
            if success:
                log.info(f"Parasite reminder sent successfully to user: {tg_id}")
            else:
                log.error(f"Failed to send parasite reminder to user {tg_id}")
        except Exception as e:
            log.error(f"Failed to send parasite reminder - {tg_id}, {e}")

@celery_app.task
def send_fleas_ticks_reminder(telegram_ids: list[int], pet_name: str):
    message = f"⚠️Напоминание: пора сделать обработку от блох и клещей для питомца {pet_name}!"
    for tg_id in telegram_ids:
        try:
            success = send_reminder_sync(tg_id, message)
            if success:
                log.info(f"Fleas & Ticks reminder sent successfully to user: {tg_id}")
            else:
                log.error(f"Failed to send Fleas & Ticks reminder to user {tg_id}")
        except Exception as e:
            log.error(f"Failed to send fleas & ticks reminder - {tg_id}, {e}")
