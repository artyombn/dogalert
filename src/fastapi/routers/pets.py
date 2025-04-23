import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session

from src.schemas.pet import (
    Pet as PetSchema,
    PetCreate,
    PetUpdate,
    PetListResponse,
    PetOwners,
    PetOwnersResponse,
    PetReports,
    PetReportsResponse,
    PetPhoto as PetPhotoSchema,
    PetPhotosResponse,
    PetPhotoCreate,
)

from src.services.pet_service import PetServices
from src.services.pet_photo_service import PetPhotoServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/pets",
    tags=["Pets"],
)

@router.get("/", summary="Get all pets", response_model=PetListResponse)
async def get_pets_list(session: AsyncSession = Depends(get_async_session)) -> PetListResponse:
    db_pets = await PetServices.get_all_pets(session)
    return PetListResponse(
        total_pets=len(db_pets),
        pets=[PetSchema.model_validate(pet) for pet in db_pets],
    )

@router.post("/create", summary="Pet creation", response_model=PetSchema)
async def create_pet(
        owner_id: int,
        pet_data: PetCreate,
        session: AsyncSession = Depends(get_async_session),
) -> PetSchema:
    new_pet = await PetServices.create_pet(owner_id, pet_data, session)
    if new_pet is None:
        raise HTTPException(status_code=404, detail=f"User not found")
    return PetSchema.model_validate(new_pet)

@router.get("/{pet_id}", summary="Get Pet by pet id", response_model=PetSchema)
async def get_pet_by_petid(
        pet_id: int,
        session: AsyncSession = Depends(get_async_session)
) -> PetSchema:
    db_pet = await PetServices.find_one_or_none_by_id(pet_id, session)
    if db_pet is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")
    return PetSchema.model_validate(db_pet)

@router.patch("/update/{pet_id}", summary="Update Pet by pet id", response_model=PetSchema)
async def update_pet(
        pet_id: int,
        pet_data: PetUpdate,
        session: AsyncSession = Depends(get_async_session),
) -> PetSchema:
    updated_pet = await PetServices.update_pet(pet_id, pet_data, session)
    if updated_pet is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")
    return PetSchema.model_validate(updated_pet)

@router.delete("/delete/{pet_id}", summary="Delete Pet by pet id", response_model=dict)
async def delete_pet(
        pet_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    pet = await PetServices.delete_pet(pet_id, session)
    if pet is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")
    return {"message": f"Pet with id = {pet_id} deleted"}

@router.get("/{pet_id}/owners", summary="Get Pet Owners", response_model=PetOwnersResponse)
async def get_pet_owners(
        pet_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> PetOwnersResponse:
    db_owners = await PetServices.get_pet_owners(pet_id, session)

    if db_owners is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")

    pet_owners = PetOwners(owners=db_owners)
    return PetOwnersResponse(
        total_owners=len(pet_owners.owners),
        owners=pet_owners.owners,
    )

@router.get("/{pet_id}/reports", summary="Get Pet Reports", response_model=PetReportsResponse)
async def get_pet_reports(
        pet_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> PetReportsResponse:
    db_reports = await PetServices.get_pet_reports(pet_id, session)

    if db_reports is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")

    pet_reports = PetReports(reports=db_reports)
    return PetReportsResponse(
        total_reports=len(pet_reports.reports),
        reports=pet_reports.reports,
    )

@router.get("/{pet_id}/photos", summary="Get Pet Photos", response_model=PetPhotosResponse)
async def get_all_pet_photos(
        pet_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> PetPhotosResponse:
    db_pet_photos = await PetPhotoServices.get_all_pet_photos(pet_id, session)
    if db_pet_photos is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")
    return PetPhotosResponse(
        total_photos=len(db_pet_photos),
        photos=[PetPhotoSchema.model_validate(photo) for photo in db_pet_photos],
    )

@router.post("/{pet_id}/photos/create", summary="Add Pet Photo", response_model=PetPhotoSchema)
async def create_pet_photo(
        pet_id: int,
        pet_photo_data: PetPhotoCreate,
        session: AsyncSession = Depends(get_async_session),
) -> PetPhotoSchema:
    new_pet_photo = await PetPhotoServices.create_pet_photo(pet_id, pet_photo_data, session)
    if new_pet_photo is None:
        raise HTTPException(status_code=404, detail=f"Pet not found")
    return PetPhotoSchema.model_validate(new_pet_photo)

@router.delete("/{pet_id}/photos/{photo_id}/delete", summary="Delete Pet Photo", response_model=dict)
async def delete_pet_photo(
        pet_id: int,
        photo_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    pet_photo = await PetPhotoServices.delete_pet_photo(photo_id, session)
    if pet_photo is None:
        raise HTTPException(status_code=404, detail=f"Pet Photo not found")
    return {"message": f"Pet Photo with id = {photo_id} deleted"}