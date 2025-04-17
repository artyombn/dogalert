import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.user import User as User_db
from src.schemas.user import UserCreate


logger = logging.getLogger(__name__)


class UserServices:
    @classmethod
    async def get_all_users(
            cls,
            session: AsyncSession,
    ) -> Sequence[User_db]:
        query = select(User_db).options(
            selectinload(User_db.pets),
            selectinload(User_db.reports),
        )
        users = await session.execute(query)
        return users.scalars().all()

    @classmethod
    async def find_one_or_none_by_tgid(cls, telegram_id: int, session: AsyncSession) -> Sequence[User_db]:
        query = (select(User_db).
        where(User_db.telegram_id == telegram_id).
        options(
            selectinload(User_db.pets),
            selectinload(User_db.reports),
        )
        )
        user = await session.execute(query)
        return user.scalar_one_or_none()

    @classmethod
    async def create_user(
            cls,
            user_data: UserCreate,
            session: AsyncSession,
            telegram_id: int,
    ) -> User_db:
        db_user = User_db(**user_data.model_dump(), telegram_id=telegram_id)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(User_db)
            .options(selectinload(User_db.pets), selectinload(User_db.reports))
            .where(User_db.id == db_user.id),
        )
        return result.scalar_one()

