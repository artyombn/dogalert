import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.pet import Pet as Pet_db
from src.database.models.pet import PetPhoto as PetPhoto_db
from src.schemas.pet import PetPhotoCreate

logger = logging.getLogger(__name__)


class PetPhotoServices:
    @classmethod
    async def get_all_pet_photos(
            cls,
            pet_id: int,
            session: AsyncSession,
    ) -> Sequence[PetPhoto_db] | None:
        query = select(PetPhoto_db).filter_by(pet_id=pet_id)
        pet_photos = await session.execute(query)
        pet_query = await session.execute(select(Pet_db).filter_by(id=pet_id))
        pet_exists = pet_query.scalar_one_or_none()

        if pet_exists is None:
            return None

        return pet_photos.scalars().all()

    @classmethod
    async def create_pet_photo(
            cls,
            pet_id: int,
            pet_photo_data: PetPhotoCreate,
            session: AsyncSession,
    ) -> PetPhoto_db | None:
        pet_photo_dict = pet_photo_data.model_dump()

        pet_query = await session.execute(select(Pet_db).filter_by(id=pet_id))
        pet_exists = pet_query.scalar_one_or_none()

        if pet_exists is None:
            return None

        new_pet_photo = PetPhoto_db(**pet_photo_dict)
        new_pet_photo.pet = pet_exists

        session.add(new_pet_photo)

        try:
            await session.commit()
            await session.refresh(new_pet_photo)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to add new Pet photo: {str(e)}")

        return new_pet_photo

    @classmethod
    async def delete_pet_photo(cls, photo_id: int, session: AsyncSession) -> bool | None:
        query = select(PetPhoto_db).filter_by(id=photo_id)
        result = await session.execute(query)
        photo = result.scalar_one_or_none()

        if photo is None:
            return None

        await session.delete(photo)

        try:
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to delete Pet Photo: {str(e)}")
