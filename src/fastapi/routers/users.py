from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.user import User
from src.services.user_service import UserServices

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# @router.get("/", summary="Get all users", response_model=List[User])
@router.get("/", summary="Get all users")
async def get_users_list(session: AsyncSession = Depends(get_async_session)):
    return await UserServices.get_all_users(session)