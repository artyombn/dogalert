import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, Query

from src.database.db_session import get_async_session
from src.schemas.report import Report as ReportSchema
from src.schemas.report import ReportListResponse, ReportCreate, ReportUpdate
from src.services.pet_service import PetServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

@router.get("/", summary="Get all reports", response_model=ReportListResponse)
async def get_reports_list(session: AsyncSession = Depends(get_async_session)) -> ReportListResponse:
    db_reports = await ReportServices.get_all_reports(session)
    return ReportListResponse(
        total_reports=len(db_reports),
        reports=[ReportSchema.model_validate(report) for report in db_reports],
    )

@router.post("/create", summary="Report creation", response_model=ReportSchema)
async def create_report(
        report_data: ReportCreate,
        user_id: int = Query(..., description="User ID"),
        pet_id: int = Query(..., description="Pet ID"),
        session: AsyncSession = Depends(get_async_session),
) -> ReportSchema:

    user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    pet = await PetServices.find_one_or_none_by_id(pet_id, session)

    if user is None or pet is None:
        raise HTTPException(status_code=404, detail="User or pet not found")

    new_report = await ReportServices.create_report(report_data, user.id, pet.id, session)
    if new_report is None:
        raise HTTPException(status_code=409, detail="Active report already exists for this pet")

    return ReportSchema.model_validate(new_report)
