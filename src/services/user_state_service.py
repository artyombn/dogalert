from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.user import User as User_db


class BaseStates(str, Enum):
    REGISTER = "register"
    FILL_PET_PROFILE = "fill_pet_profile"
    CREATE_ADS = "create_ads"
    NOTHING = "nothing"

class UserStateServices:
    @classmethod
    async def get_current_state(
            cls,
            telegram_id: int,
            session: AsyncSession,
    ) -> BaseStates | None:
        result = await session.execute(select(User_db).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return BaseStates(user.state)

    @classmethod
    async def update_state(
            cls,
            telegram_id: int,
            new_state: BaseStates,
            session: AsyncSession,
    ) -> User_db | None:
        result = await session.execute(select(User_db).filter_by(telegram_id=telegram_id))
        user = result.scalar_one_or_none()
        if user is None:
            return None

        user.state = new_state.value
        try:
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to update user: {str(e)}")

        return user


