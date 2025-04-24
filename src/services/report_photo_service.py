import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.report import Report as Report_db
from src.database.models.report import ReportPhoto as ReportPhoto_db

logger = logging.getLogger(__name__)


class ReportPhotoServices:
    @classmethod
    async def get_all_report_photos(
            cls,
            report_id: int,
            session: AsyncSession,
    ) -> Sequence[ReportPhoto_db] | None:
        query = select(ReportPhoto_db).filter_by(report_id=report_id)
        report_photos = await session.execute(query)
        report_query = await session.execute(select(Report_db).filter_by(id=report_id))
        report_exists = report_query.scalar_one_or_none()

        if report_exists is None:
            return None

        return report_photos.scalars().all()
