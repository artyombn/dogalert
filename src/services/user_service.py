from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.user import User as User_db
from src.schemas.user import UserCreate


class UserServices:
    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> Sequence[User_db]:
        query = select(User_db).options(
            selectinload(User_db.pets),
            selectinload(User_db.reports)
        )
        users = await session.execute(query)
        return users.scalars().all()

    @classmethod
    async def create_user(cls, user_data: UserCreate, session: AsyncSession, telegram_id: int) -> User_db:
        db_user = User_db(**user_data.model_dump(), telegram_id=telegram_id)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(User_db)
            .options(selectinload(User_db.pets), selectinload(User_db.reports))
            .where(User_db.id == db_user.id)
        )
        return result.scalar_one()
