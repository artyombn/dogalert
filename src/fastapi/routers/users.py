import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.db_session import get_async_session
from src.schemas.user import User as UserSchema
from src.schemas.user import UserCreate, UserUpdate, UserListResponse
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

@router.get("/", summary="Get all users", response_model=UserListResponse)
async def get_users_list(session: AsyncSession = Depends(get_async_session)) -> UserListResponse:
    db_users = await UserServices.get_all_users(session)
    return UserListResponse(
        total_users=len(db_users),
        users=[UserSchema.model_validate(user) for user in db_users],
    )

@router.get("/{telegram_id}", summary="Get User by telegram id", response_model=UserSchema)
async def get_user_by_tgid(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    db_user = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
    if db_user is None:
        raise HTTPException(status_code=404, detail=f"User not found")
    return UserSchema.model_validate(db_user)

@router.post("/create", summary="User creation", response_model=UserSchema)
async def create_user(
        user_data: UserCreate,
        telegram_id: int = 1,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    new_db_user = await UserServices.create_user(user_data, session, telegram_id)
    if new_db_user is None:
        raise HTTPException(status_code=409, detail=f"User with telegram_id={telegram_id} already exists")
    return UserSchema.model_validate(new_db_user)

@router.patch("/update/{telegram_id}", summary="Update User by telegram id", response_model=UserSchema)
async def update_user(
        user_data: UserUpdate,
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    updated_user = await UserServices.update_user(user_data, session, telegram_id)
    if updated_user is None:
        raise HTTPException(status_code=409, detail=f"User not found")
    return UserSchema.model_validate(updated_user)


