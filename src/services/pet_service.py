import logging
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.celery_app.config import app
from src.database.models.pet import Pet as Pet_db
from src.database.models.user import User as User_db
from src.schemas.pet import PetCreate, PetUpdate
from src.services.reminder_service import ReminderServices

logger = logging.getLogger(__name__)


class PetServices:
    @classmethod
    async def get_all_pets(
            cls,
            session: AsyncSession,
    ) -> Sequence[Pet_db]:
        pets = await session.execute(select(Pet_db))
        return pets.scalars().all()

    @classmethod
    async def create_pet(
            cls,
            owner_id: int,
            pet_data: PetCreate,
            session: AsyncSession,
    ) -> Pet_db | None:
        pet_dict = pet_data.model_dump()

        user_query = select(User_db).filter_by(id=owner_id)
        result = await session.execute(user_query)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        new_pet = Pet_db(**pet_dict)
        new_pet.owners.append(user)

        session.add(new_pet)

        try:
            await session.commit()
            await session.refresh(new_pet)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create pet: {str(e)}")

        return new_pet

    @classmethod
    async def find_one_or_none_by_id(cls, pet_id: int, session: AsyncSession) -> Pet_db | None:
        query = (
            select(Pet_db)
            .options(selectinload(Pet_db.owners))
            .filter_by(id=pet_id)
        )
        pet = await session.execute(query)
        return pet.scalar_one_or_none()

    @classmethod
    async def update_pet(
            cls,
            pet_id: int,
            pet_data: PetUpdate,
            session: AsyncSession,
    ) -> Pet_db | None:
        query = (
            select(Pet_db).
            filter_by(id=pet_id)
        )

        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None:
            return None

        for field, value in pet_data.model_dump(exclude_unset=True).items():
            setattr(pet, field, value)

        try:
            await session.commit()
            await session.refresh(pet)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to update pet: {str(e)}")

        return pet

    @classmethod
    async def delete_pet(cls, pet_id: int, session: AsyncSession) -> bool | None:
        query = select(Pet_db).filter_by(id=pet_id)
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None:
            return None

        await session.delete(pet)

        try:
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to delete pet: {str(e)}")

    @classmethod
    async def get_pet_owners(cls, pet_id: int, session: AsyncSession) -> list | None:
        query = (
            select(Pet_db)
            .where(Pet_db.id == pet_id)
            .options(selectinload(Pet_db.owners))
        )
        result = await session.execute(query)
        pet = result.scalar_one_or_none()
        if pet is None:
            return None
        return pet.owners

    @classmethod
    async def get_pet_reports(cls, pet_id: int, session: AsyncSession) -> list | None:
        query = (
            select(Pet_db)
            .where(Pet_db.id == pet_id)
            .options(selectinload(Pet_db.reports))
        )
        result = await session.execute(query)
        pet = result.scalar_one_or_none()
        if pet is None:
            return None
        return pet.reports

    @classmethod
    async def get_all_pet_uids(cls, session: AsyncSession) -> Sequence[int]:
        result = await session.execute(select(Pet_db.id))
        return result.scalars().all()

    @classmethod
    async def update_vaccination_dates(
            cls,
            pet_id: int,
            last_vaccination: datetime,
            next_vaccination: datetime,
            session: AsyncSession
    ) -> list[datetime] | None:
        query = (
            select(Pet_db)
            .where(Pet_db.id == pet_id)
            .options(selectinload(Pet_db.owners))
        )
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None:
            return None

        if last_vaccination:
            try:
                pet.last_vaccination = last_vaccination
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet last_vaccination: {str(e)}")

        if next_vaccination:
            try:
                if pet.vaccination_reminder_task_id:
                    app.control.revoke(pet.vaccination_reminder_task_id, terminate=True)
                    pet.vaccination_reminder_task_id = None

                pet.next_vaccination = next_vaccination
                await session.commit()

                task_id = await ReminderServices.schedule_vaccination_reminder(pet.id, session)
                pet.vaccination_reminder_task_id = task_id
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet next_vaccination: {str(e)}")

        return [last_vaccination, next_vaccination]

    @classmethod
    async def update_parasite_dates(
            cls,
            pet_id: int,
            last_parasite_treatment: datetime,
            next_parasite_treatment: datetime,
            session: AsyncSession
    ) -> list[datetime] | None:
        query = (
            select(Pet_db)
            .where(Pet_db.id == pet_id)
            .options(selectinload(Pet_db.owners))
        )
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None:
            return None

        if last_parasite_treatment:
            try:
                pet.last_parasite_treatment = last_parasite_treatment
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet last_parasite_treatment: {str(e)}")

        if next_parasite_treatment:
            try:
                if pet.parasite_reminder_task_id:
                    app.control.revoke(pet.parasite_reminder_task_id, terminate=True)
                    pet.parasite_reminder_task_id = None

                pet.next_parasite_treatment = next_parasite_treatment
                await session.commit()

                task_id = await ReminderServices.schedule_parasite_reminder(pet.id, session)
                pet.parasite_reminder_task_id = task_id
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet next_parasite_treatment: {str(e)}")

        return [last_parasite_treatment, next_parasite_treatment]

    @classmethod
    async def update_fleas_ticks_dates(
            cls,
            pet_id: int,
            last_fleas_ticks_treatment: datetime,
            next_fleas_ticks_treatment: datetime,
            session: AsyncSession
    ) -> list[datetime] | None:
        query = (
            select(Pet_db)
            .where(Pet_db.id == pet_id)
            .options(selectinload(Pet_db.owners))
        )
        result = await session.execute(query)
        pet = result.scalar_one_or_none()

        if pet is None:
            return None

        if last_fleas_ticks_treatment:
            try:
                pet.last_fleas_ticks_treatment = last_fleas_ticks_treatment
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet last_fleas_ticks_treatment: {str(e)}")

        if next_fleas_ticks_treatment:
            try:
                if pet.fleas_ticks_reminder_task_id:
                    app.control.revoke(pet.fleas_ticks_reminder_task_id, terminate=True)
                    pet.fleas_ticks_reminder_task_id = None

                pet.next_fleas_ticks_treatment = next_fleas_ticks_treatment
                await session.commit()

                task_id = await ReminderServices.schedule_fleas_ticks_reminder(pet.id, session)
                pet.fleas_ticks_reminder_task_id = task_id
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise Exception(f"Failed to update pet next_fleas_ticks_treatment: {str(e)}")

        return [last_fleas_ticks_treatment, next_fleas_ticks_treatment]
