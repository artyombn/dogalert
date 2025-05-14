import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas import Pet as Pet_schema
from src.schemas import Report as Report_schema
from src.schemas.geo import Geolocation
from src.schemas.user import User as UserSchema
from src.schemas.user import (
    UserCreate,
    UserListResponse,
    UserPet,
    UserPetsResponse,
    UserReport,
    UserReportsResponse,
    UserUpdate,
)
from src.services.user_service import UserServices
from src.web.dependencies.city_geo_handles import get_city_from_geo, extract_city_name

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/users",
    tags=["API Users"],
)

@router.get("/", summary="Get all users", response_model=UserListResponse)
async def get_users_list(session: AsyncSession = Depends(get_async_session)) -> UserListResponse:
    db_users = await UserServices.get_all_users(session)
    return UserListResponse(
        total_users=len(db_users),
        users=[UserSchema.model_validate(user) for user in db_users],
    )

@router.post("/create", summary="User creation", response_model=UserSchema)
async def create_user(
        user_data: UserCreate,
        telegram_id: int = 1,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    new_db_user = await UserServices.create_user(user_data, session, telegram_id)
    if new_db_user is None:
        raise HTTPException(
            status_code=409,
            detail=f"User with telegram_id={telegram_id} already exists",
        )
    return UserSchema.model_validate(new_db_user)

@router.get("/tg/{telegram_id}", summary="Get User by telegram id", response_model=UserSchema)
async def get_user_by_tgid(
        telegram_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    db_user = await UserServices.find_one_or_none_by_tgid(telegram_id, session)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema.model_validate(db_user)

@router.patch("/update/{user_id}", summary="Update User by id", response_model=UserSchema)
async def update_user(
        user_id: int,
        user_data: UserUpdate,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    updated_user = await UserServices.update_user(user_id, user_data, session)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema.model_validate(updated_user)

@router.delete("/delete/{user_id}", summary="Delete User by user id", response_model=dict)
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    user = await UserServices.delete_user(user_id, session)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User with id = {user_id} deleted"}

@router.get("/{user_id}/pets", summary="Get User Pets", response_model=UserPetsResponse)
async def get_user_pets(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserPetsResponse:
    db_pets = await UserServices.get_all_user_pets(user_id, session)

    if db_pets is None:
        raise HTTPException(status_code=404, detail="User not found")

    pets_schema = [Pet_schema.model_validate(pet) for pet in db_pets]
    user_pets = UserPet(pets=pets_schema)
    return UserPetsResponse(
        total_pets=len(user_pets.pets),
        pets=user_pets.pets,
    )

@router.get("/{user_id}/reports", summary="Get User Reports", response_model=UserReportsResponse)
async def get_user_reports(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserReportsResponse:
    db_reports = await UserServices.get_all_user_reports(user_id, session)
    if db_reports is None:
        raise HTTPException(status_code=404, detail="User not found")

    reports_schema = [Report_schema.model_validate(report) for report in db_reports]
    user_reports = UserReport(reports=reports_schema)

    return UserReportsResponse(
        total_reports=len(user_reports.reports),
        reports=user_reports.reports,
    )

@router.get("/{user_id}/geolocation", summary="Get User Geolocaion", response_model=Geolocation)
async def get_user_geolocation(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> Geolocation:
    user_geo = await UserServices.get_user_geolocation(user_id, session)

    if user_geo is None:
        raise HTTPException(status_code=404, detail="User's geolocation not found")
    return user_geo

@router.get("/{user_id}/geolocation/city", summary="Get User's city", response_model=dict)
async def get_user_geo_city(
        request: Request,
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict | None:
    user_geo = await UserServices.get_user_geolocation(user_id, session)

    if user_geo is None:
        raise HTTPException(status_code=404, detail="User's geolocation not found")

    aiohttp_session = request.app.state.aiohttp_session
    coordinates = (user_geo.home_location[6:-1]).split(" ")
    request_city = await get_city_from_geo(
        lat=float(coordinates[1]),
        lon=float(coordinates[0]),
        session=aiohttp_session,
    )
    city = extract_city_name(request_city)
    if not city:
        return None
    return {"user_geo": user_geo, "city": city}

@router.get("/{user_id}", summary="Get User by id", response_model=UserSchema)
async def get_user_by_id(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> UserSchema:
    db_user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema.model_validate(db_user)
