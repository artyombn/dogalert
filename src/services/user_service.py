from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User as User_db
from src.schemas.user import UserCreate


class UserServices:
    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> Sequence[User_db]:
        query = select(User_db)
        users = await session.execute(query)
        return users.scalars().all()

    @classmethod
    async def create_user(cls, user_data: UserCreate, session: AsyncSession) -> User_db:
        db_user = User_db(**user_data.model_dump())
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        return db_user
