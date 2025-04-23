import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.pet import Pet as Pet_db, PetPhoto as PetPhoto_db

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