import logging

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Cookie, Depends
from src.database.db_session import get_async_session
from src.schemas import User as User_schema
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

async def get_current_user_from_cookie(
    user_id: int = Cookie(None),
    session: AsyncSession = Depends(get_async_session),
) -> User_schema | None:
    if user_id is None:
        return None

    user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user is None:
        return None
    return User_schema.model_validate(user)
