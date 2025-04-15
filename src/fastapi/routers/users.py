from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends
from src.database.db_session import get_async_session
from src.schemas.user import User as UserSchema
from src.schemas.user import UserCreate
from src.services.user_service import UserServices

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/", summary="Get all users", response_model=list[UserSchema])
async def get_users_list(session: AsyncSession = Depends(get_async_session)) -> list[UserSchema]:
    db_users = await UserServices.get_all_users(session)
    return [UserSchema.model_validate(user) for user in db_users]

@router.post("/create", summary="User creation", response_model=UserSchema)
async def create_user(
        user_data: UserCreate,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    new_db_user = await UserServices.create_user(user_data, session)
    return UserSchema.model_validate(new_db_user)
