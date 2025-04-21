import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.db_session import get_async_session
from src.schemas.user import User as UserSchema
from src.schemas.user import UserCreate, UserUpdate, UserListResponse, UserPetsResponse, UserReportsResponse, UserPet, UserReport
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

@router.get("/tg/{telegram_id}", summary="Get User by telegram id", response_model=UserSchema)
async def get_user_by_tgid(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    db_user = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
    if db_user is None:
        raise HTTPException(status_code=404, detail=f"User not found")
    return UserSchema.model_validate(db_user)

@router.get("/{user_id}", summary="Get User by id", response_model=UserSchema)
async def get_user_by_id(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    db_user = await UserServices.find_one_or_none_by_user_id(user_id, session)
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

@router.patch("/update/{user_id}", summary="Update User by id", response_model=UserSchema)
async def update_user(
        user_id: int,
        user_data: UserUpdate,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    updated_user = await UserServices.update_user(user_id, user_data, session)
    if updated_user is None:
        raise HTTPException(status_code=404, detail=f"User not found")
    return UserSchema.model_validate(updated_user)

@router.delete("/delete/{user_id}", summary="Delete User by user id", response_model=dict)
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    user = await UserServices.delete_user(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User not found")
    return {"message": f"User with id = {user_id} deleted"}

@router.get("/{user_id}/pets", summary="Get User Pets", response_model=UserPetsResponse)
async def get_user_pets(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserPetsResponse:
    db_pets = await UserServices.get_all_user_pets(user_id, session)

    if db_pets is None:
        raise HTTPException(status_code=404, detail=f"User not found")

    user_pets = UserPet(pets=db_pets)
    return UserPetsResponse(
        total_pets=len(user_pets.pets),
        pets=user_pets.pets,
    )

