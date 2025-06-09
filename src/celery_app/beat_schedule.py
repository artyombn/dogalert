import logging
from datetime import date

from src.services.pet_service import PetServices

from .config import celery_app
from .reminder_tasks import (
    send_fleas_ticks_reminder,
    send_parasite_reminder,
    send_vaccination_reminder,
)
from .sync_database import celery_sync_session_maker

log = logging.getLogger(__name__)

@celery_app.task
def get_pets_for_reminders() -> dict:
    """
    Получаем из БД всех Pet у которых

    pet.next_vaccination == today
    pet.next_parasite_treatment == today
    pet.next_fleas_ticks_treatment == today

    И если находим таких, то отправляем соответствующие задачи
    send_vaccination_reminder, send_parasite_reminder, send_fleas_ticks_reminder
    """
    log.info("Start daily pet reminders check")
    try:
        with celery_sync_session_maker() as session:
            today = date.today()
            log.info(f"Today date: {today}")

            vacc_pets = PetServices.get_pets_by_vaccination_date(today, session)
            parasite_pets = PetServices.get_pets_by_parasite_date(today, session)
            fleas_ticks_pets = PetServices.get_pets_by_fleas_ticks_date(today, session)

            vacc_sent = 0
            for pet in vacc_pets:
                telegram_ids = [owner.telegram_id for owner in pet.owners]
                send_vaccination_reminder.delay(telegram_ids, pet.name)
                vacc_sent += 1

            parasite_sent = 0
            for pet in parasite_pets:
                telegram_ids = [owner.telegram_id for owner in pet.owners]
                send_parasite_reminder.delay(telegram_ids, pet.name)
                parasite_sent += 1

            fleas_ticks_sent = 0
            for pet in fleas_ticks_pets:
                telegram_ids = [owner.telegram_id for owner in pet.owners]
                send_fleas_ticks_reminder.delay(telegram_ids, pet.name)
                fleas_ticks_sent += 1

            result = {
                "date": today.isoformat(),
                "vaccination_sent": vacc_sent,
                "parasite_sent": parasite_sent,
                "fleas_ticks_sent": fleas_ticks_sent,
            }

            log.info(f"Reminders summary: {result}")
            return result

    except Exception as e:
        log.error(f"Daily pet reminders FAILED: {e}")
        raise
