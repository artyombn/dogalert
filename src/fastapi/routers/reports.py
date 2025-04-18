import logging
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from src.database.db_session import get_async_session
from src.schemas.report import Report as ReportSchema
from src.schemas.report import ReportListResponse, ReportCreate, ReportUpdate
from src.services.report_service import ReportServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

@router.get("/", summary="Get all pets", response_model=ReportListResponse)
async def get_reports_list(session: AsyncSession = Depends(get_async_session)) -> ReportListResponse:
    db_reports = await ReportServices.get_all_reports(session)
    return ReportListResponse(
        total_reports=len(db_reports),
        reports=[ReportSchema.model_validate(report) for report in db_reports],
    )