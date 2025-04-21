import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.user import User as User_db
from src.schemas.user import UserCreate, UserUpdate


logger = logging.getLogger(__name__)


class UserServices:
    @classmethod
    async def get_all_users(
            cls,
            session: AsyncSession,
    ) -> Sequence[User_db]:
        users = await session.execute(select(User_db))
        return users.scalars().all()

    @classmethod
    async def find_one_or_none_by_tgid(cls, telegram_id: int, session: AsyncSession) -> User_db:
        query = (
            select(User_db).
            filter_by(telegram_id=telegram_id)
        )
        user = await session.execute(query)
        return user.scalar_one_or_none()

    @classmethod
    async def find_one_or_none_by_user_id(cls, user_id: int, session: AsyncSession) -> User_db:
        query = (
            select(User_db).
            filter_by(id=user_id)
        )
        user = await session.execute(query)
        return user.scalar_one_or_none()

    @classmethod
    async def create_user(
            cls,
            user_data: UserCreate,
            session: AsyncSession,
            telegram_id: int,
    ) -> User_db | None:
        query = select(User_db).filter_by(telegram_id=telegram_id)
        result = await session.execute(query)
        user_exist = result.scalar_one_or_none()

        if user_exist:
            return None

        db_user = User_db(**user_data.model_dump(exclude_unset=True), telegram_id=telegram_id)
        session.add(db_user)

        try:
            await session.commit()
            await session.refresh(db_user)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create user: {str(e)}")

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(User_db).
            filter_by(id=db_user.id)
        )
        user = result.scalar_one()

        return user

    @classmethod
    async def update_user(
            cls,
            user_id: int,
            user_data: UserUpdate,
            session: AsyncSession,
    ) -> User_db | None:
        query = (
            select(User_db).
            filter_by(id=user_id)
        )

        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        for field, value in user_data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)

        try:
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to update user: {str(e)}")

        return user

    @classmethod
    async def delete_user(cls, user_id: int, session: AsyncSession) -> bool | None:
        query = select(User_db).filter_by(id=user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            return None

        await session.delete(user)

        try:
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to delete user: {str(e)}")

    @classmethod
    async def get_all_user_pets(cls, user_id: int, session: AsyncSession) -> list | None:
        query = (
            select(User_db)
            .where(User_db.id == user_id)
            .options(selectinload(User_db.pets))
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return user.pets

    @classmethod
    async def get_all_user_reports(cls, user_id: int, session: AsyncSession) -> User_db:
        query = (
            select(User_db)
            .where(User_db.id == user_id)
            .options(selectinload(User_db.reports))
        )
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return user.reports







