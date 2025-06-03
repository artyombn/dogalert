import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.celery_app.reminder_tasks import (
    send_vaccination_reminder,
    send_parasite_reminder,
    send_fleas_ticks_reminder,
)
from src.database.models import Pet as Pet_db


log = logging.getLogger(__name__)


class ReminderServices:
    @classmethod
    async def schedule_vaccination_reminder(cls, pet_id: int, session: AsyncSession) -> int:
        query = select(Pet_db).filter_by(id=pet_id)
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None or pet.next_vaccination is None or pet.owners is None:
            return None

        telegram_ids = [user.telegram_id for user in pet.owners]

        schedule_task = send_vaccination_reminder.apply_async(
            args=[telegram_ids, pet.name],
            eta=pet.next_vaccination
        )
        log.info(f"Scheduled vaccination reminder. Pet: {pet.id}, next vaccination: {pet.next_vaccination}")
        return schedule_task.id

    @classmethod
    async def schedule_parasite_reminder(cls, pet_id: int, session: AsyncSession) -> int:
        query = select(Pet_db).filter_by(id=pet_id)
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None or pet.next_parasite_treatment is None or pet.owners is None:
            return None

        telegram_ids = [user.telegram_id for user in pet.owners]

        schedule_task = send_parasite_reminder.apply_async(
            args=[telegram_ids, pet.name],
            eta=pet.next_parasite_treatment
        )
        log.info(f"Scheduled parasite reminder. Pet: {pet.id},  next parasite: {pet.next_parasite_treatment}")
        return schedule_task.id

    @classmethod
    async def schedule_fleas_ticks_reminder(cls, pet_id: int, session: AsyncSession) -> int:
        query = select(Pet_db).filter_by(id=pet_id)
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None or pet.next_fleas_ticks_treatment is None or pet.owners is None:
            return None

        telegram_ids = [user.telegram_id for user in pet.owners]

        schedule_task = send_fleas_ticks_reminder.apply_async(
            args=[telegram_ids, pet.name],
            eta=pet.next_fleas_ticks_treatment
        )
        log.info(f"Scheduled fleas ticks reminder. Pet: {pet.id},  next fleas ticks: {pet.next_fleas_ticks_treatment}")
        return schedule_task.id



