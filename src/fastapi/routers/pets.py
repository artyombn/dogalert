import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.db_session import get_async_session
from src.schemas.pet import Pet as PetSchema
from src.schemas.pet import PetListResponse
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