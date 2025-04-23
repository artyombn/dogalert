import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.pet import Pet as Pet_db, PetPhoto as PetPhoto_db
from src.schemas.pet import PetPhotoCreate

logger = logging.getLogger(__name__)


class PetPhotoServices:
    @classmethod
    async def get_all_pet_photos(
            cls,
            pet_id: int,
            session: AsyncSession,
    ) -> Sequence[PetPhoto_db]:
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
    ) -> PetPhoto_db:
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

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(PetPhoto_db).
            filter_by(id=new_pet_photo.id)
        )
        pet_photo = result.scalar_one()

        return pet_photo