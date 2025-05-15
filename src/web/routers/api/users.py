import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.database.models.geo import GeoFilterType
from src.schemas import Pet as Pet_schema
from src.schemas import Report as Report_schema
from src.schemas.geo import Geolocation, Coordinates, GeolocationUpdate
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
from src.services.geo_service import GeoServices
from src.services.user_service import UserServices
from src.web.dependencies.city_geo_handles import extract_city_name, get_city_from_geo, check_city

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

@router.put("/update/geo/{user_id}", response_model=None, include_in_schema=True)
async def update_user_geolocation(
        request: Request,
        user_id: int,
        coordinates: Coordinates,
        filter_type: GeoFilterType,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    aiohttp_session = request.app.state.aiohttp_session

    user_exists = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user_exists is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )

    async with asyncio.TaskGroup() as tg:
        user_geo_exists_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))
        requested_user_city_task = tg.create_task(
            get_city_from_geo(
                lat=coordinates.lat,
                lon=coordinates.lon,
                session=aiohttp_session,
            ),
        )

    user_geo_exists = user_geo_exists_task.result()
    requested_user_city = requested_user_city_task.result()

    logger.info(f"USER GEO EXISTS = {user_geo_exists.__dict__}")

    if not user_geo_exists:
        return JSONResponse(
            content={"status": "error", "message": "Геолокация не найдена"},
            status_code=404,
        )

    if not requested_user_city:
        return JSONResponse(
            content={"status": "error", "message": "Не удалось найти ваш город"},
            status_code=404,
        )

    if not check_city(requested_user_city):
        return JSONResponse(
            content={"status": "error", "message": "Город не найден в списке городов России"},
            status_code=404,
        )

    user_city = extract_city_name(requested_user_city)
    logger.info(f"USER GEO EXTRACTED = {user_city}")
    try:
        geo_data = GeolocationUpdate(
            region=user_city or "Moscow",
            home_location=f"POINT({coordinates.lon} {coordinates.lat})",
            filter_type=filter_type,
        )
        logger.info(f"GEO DATA = {geo_data.__dict__}")
    except ValidationError as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка валидации. {e}"},
            status_code=500,
        )

    try:
        await GeoServices.update_geolocation(
            user_id=user_id,
            geo_data=geo_data,
            session=session,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка при обновлении {e}"},
            status_code=500,
        )
    return JSONResponse(
        content={
            "status": "success",
            "message": "Гео данные успешно обновлены",
        },
        status_code=200,
    )

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
    if not request_city:
        return None

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
