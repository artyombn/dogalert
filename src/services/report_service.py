import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models.report import Report as Report_db, ReportPhoto as ReportPhoto_db
from src.schemas.report import ReportCreate, ReportUpdate

logger = logging.getLogger(__name__)


class ReportServices:
    @classmethod
    async def get_all_reports(
            cls,
            session: AsyncSession,
    ) -> Sequence[Report_db]:
        query = select(Report_db).options(
            selectinload(Report_db.user),
            selectinload(Report_db.pet),
            selectinload(Report_db.photos),
        )
        reports = await session.execute(query)
        return reports.scalars().all()