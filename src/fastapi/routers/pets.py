import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.db_session import get_async_session
from src.schemas.pet import Pet as PetSchema
from src.schemas.pet import PetListResponse, PetCreate, PetUpdate
from src.services.pet_serice import PetServices

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
        pet_data: PetCreate,
        session: AsyncSession = Depends(get_async_session),
) -> PetSchema:
    new_pet = await PetServices.create_pet(pet_data, session)
    if pet_data is None:
        raise HTTPException(status_code=409, detail=f"Pet is already exists")
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
    return {"message": f"Pet with tg_id = {pet_id} deleted"}