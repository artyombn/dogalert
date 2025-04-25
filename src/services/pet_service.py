import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.pet import Pet as Pet_db
from src.database.models.user import User as User_db
from src.schemas.pet import PetCreate, PetUpdate

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
            select(Pet_db).
            filter_by(id=pet_id)
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
