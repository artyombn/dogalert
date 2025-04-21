import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.report import Report as Report_db, ReportPhoto as ReportPhoto_db, ReportStatus
from src.schemas.report import ReportCreate, ReportUpdate

logger = logging.getLogger(__name__)


class ReportServices:
    @classmethod
    async def get_all_reports(
            cls,
            session: AsyncSession,
    ) -> Sequence[Report_db]:
        query = (select(Report_db).
                 options(
            selectinload(Report_db.user),
            selectinload(Report_db.pet),
        )
                 )
        reports = await session.execute(query)
        return reports.scalars().all()

    @classmethod
    async def create_report(
            cls,
            report_data: ReportCreate,
            user_id: int,
            pet_id: int,
            session: AsyncSession,
    ) -> Report_db:
        report_dict = report_data.model_dump()
        report_dict["user_id"] = user_id
        report_dict["pet_id"] = pet_id

        query = select(Report_db).filter(
            Report_db.pet_id == pet_id,
            Report_db.status == ReportStatus.ACTIVE
        )
        result = await session.execute(query)
        active_report = result.scalars().first()

        if active_report:
            return None

        new_report = Report_db(**report_dict)
        session.add(new_report)

        try:
            await session.commit()
            await session.refresh(new_report)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create report: {str(e)}")

        # Eager load relations to avoid MissingGreenlet during serialization
        result = await session.execute(
            select(Report_db).
            filter_by(id=new_report.id)
        )
        report = result.scalar_one()

        return report

    @classmethod
    async def find_one_or_none_by_id(cls, report_id: int, session: AsyncSession) -> Report_db:
        query = (
            select(Report_db).
            filter_by(id=report_id)
        )
        report = await session.execute(query)
        return report.scalar_one_or_none()

    @classmethod
    async def update_report(
            cls,
            report_id: int,
            report_data: ReportUpdate,
            session: AsyncSession,
    ) -> Report_db | None:
        query = (
            select(Report_db).
            filter_by(id=report_id)
        )

        result = await session.execute(query)
        report = result.scalar_one_or_none()

        if report is None:
            return None

        for field, value in report_data.model_dump(exclude_unset=True).items():
            setattr(report, field, value)

        try:
            await session.commit()
            await session.refresh(report)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to update report: {str(e)}")

        return report