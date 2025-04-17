import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.pet import Pet as Pet_db
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
