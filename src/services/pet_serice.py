import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.pet import Pet as Pet_db, PetPhoto as PetPhoto_db
from src.schemas.pet import PetCreate, PetUpdate

logger = logging.getLogger(__name__)


class PetServices:
    @classmethod
    async def get_all_pets(
            cls,
            session: AsyncSession,
    ) -> Sequence[Pet_db]:
        query = select(Pet_db).options(
            selectinload(Pet_db.owners),
            selectinload(Pet_db.reports),
            selectinload(Pet_db.photos),
        )
        pets = await session.execute(query)
        return pets.scalars().all()

    @classmethod
    async def create_pet(
            cls,
            pet_data: PetCreate,
            session: AsyncSession,
    ) -> Pet_db:
        pet_dict = pet_data.model_dump(exclude={"photos"})
        logger.debug(f"Pet_dict = {pet_dict}")
        new_pet = Pet_db(**pet_dict)
        logger.debug(f"New_pet = {new_pet.__dict__}")

        logger.debug(f"pet_photos_exists? = {True if pet_data.photos else False}")
        if pet_data.photos:
            new_pet.photos = [PetPhoto_db(url=photo.url) for photo in pet_data.photos]
            logger.debug(f"New_pet_photos = {new_pet.photos}")

        logger.debug(f"----------------------------"
                     f"Before add() = {new_pet.__dict__}")
        session.add(new_pet)
        logger.debug(f"----------------------------"
                     f"After add() = {new_pet.__dict__}")

        try:
            await session.commit()
            await session.refresh(new_pet)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create pet: {str(e)}")

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(Pet_db).
            filter_by(id=new_pet.id).
            options(
                selectinload(Pet_db.owners),
                selectinload(Pet_db.reports),
                selectinload(Pet_db.photos),
            )
        )
        pet = result.scalar_one()

        return pet

    @classmethod
    async def find_one_or_none_by_id(cls, pet_id: int, session: AsyncSession) -> Pet_db:
        query = (
            select(Pet_db).
            filter_by(id=pet_id).
            options(
                selectinload(Pet_db.owners),
                selectinload(Pet_db.reports),
                selectinload(Pet_db.photos),
            )
        )
        pet = await session.execute(query)
        return pet.scalar_one_or_none()