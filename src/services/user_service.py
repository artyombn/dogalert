from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User as User_db


class UserServices:
    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> Sequence[User_db]:
        query = select(User_db)
        users = await session.execute(query)
        return users.scalars().all()
