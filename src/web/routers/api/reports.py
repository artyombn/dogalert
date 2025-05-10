import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.report import Report as ReportSchema
from src.schemas.report import (
    ReportCreate,
    ReportListResponse,
    ReportPhotoCreate,
    ReportPhotosResponse,
    ReportUpdate,
)
from src.schemas.report import ReportPhoto as ReportPhotoSchema
from src.services.pet_service import PetServices
from src.services.report_photo_service import ReportPhotoServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)

@router.get("/", summary="Get all reports", response_model=ReportListResponse)
async def get_reports_list(
        session: AsyncSession = Depends(get_async_session),
) -> ReportListResponse:
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

@router.patch("/update/{report_id}", summary="Update Report by id", response_model=ReportSchema)
async def update_report(
        report_id: int,
        report_data: ReportUpdate,
        session: AsyncSession = Depends(get_async_session),
) -> ReportSchema:
    updated_report = await ReportServices.update_report(report_id, report_data, session)
    if updated_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportSchema.model_validate(updated_report)

@router.delete("/delete/{report_id}", summary="Delete Report by id", response_model=dict)
async def delete_report(
        report_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    report = await ReportServices.delete_report(report_id, session)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": f"Report with id = {report_id} deleted"}

@router.get("/{report_id}/photos", summary="Get Report Photos", response_model=ReportPhotosResponse)
async def get_all_report_photos(
        report_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> ReportPhotosResponse:
    db_report_photos = await ReportPhotoServices.get_all_report_photos(report_id, session)
    if db_report_photos is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportPhotosResponse(
        total_photos=len(db_report_photos),
        photos=[ReportPhotoSchema.model_validate(photo) for photo in db_report_photos],
    )

@router.post(
    "/{report_id}/photos/create",
    summary="Add Report Photo",
    response_model=ReportPhotoSchema,
)
async def create_report_photo(
        report_id: int,
        report_photo_data: ReportPhotoCreate,
        session: AsyncSession = Depends(get_async_session),
) -> ReportPhotoSchema:
    new_report_photo = await ReportPhotoServices.create_report_photo(
        report_id,
        report_photo_data,
        session,
    )
    if new_report_photo is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportPhotoSchema.model_validate(new_report_photo)

@router.delete(
    "/{report_id}/photos/{photo_id}/delete",
    summary="Delete Report Photo",
    response_model=dict,
)
async def delete_report_photo(
        report_id: int,
        photo_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> dict:
    report_photo = await ReportPhotoServices.delete_report_photo(photo_id, session)
    if report_photo is None:
        raise HTTPException(status_code=404, detail="Report Photo not found")
    return {"message": f"Report Photo with id = {photo_id} deleted"}

@router.get("/{report_id}", summary="Get Report by its id", response_model=ReportSchema)
async def get_report_by_id(
        report_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> ReportSchema:
    db_report = await ReportServices.find_one_or_none_by_id(report_id, session)
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportSchema.model_validate(db_report)
