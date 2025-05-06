import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.report import Report as Report_db
from src.database.models.report import ReportPhoto as ReportPhoto_db
from src.schemas import ReportPhotoCreate

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

    @classmethod
    async def create_report_photo(
            cls,
            report_id: int,
            report_photo_data: ReportPhotoCreate,
            session: AsyncSession,
    ) -> ReportPhoto_db | None:
        report_photo_dict = report_photo_data.model_dump()

        report_query = await session.execute(select(Report_db).filter_by(id=report_id))
        report_exists = report_query.scalar_one_or_none()

        if report_exists is None:
            return None

        new_report_photo = ReportPhoto_db(**report_photo_dict)
        new_report_photo.report = report_exists

        session.add(new_report_photo)

        try:
            await session.commit()
            await session.refresh(new_report_photo)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to add new Report photo: {str(e)}")

        return new_report_photo

    @classmethod
    async def create_many_report_photos(
            cls,
            report_id: int,
            report_photo_data_list: list[ReportPhotoCreate],
            session: AsyncSession,
    ) -> list[ReportPhoto_db] | None:
        report_query = await session.execute(select(Report_db).filter_by(id=report_id))
        report_exists = report_query.scalar_one_or_none()

        if report_exists is None:
            return None

        photos = [
            ReportPhoto_db(report_id=report_id, **photo.model_dump())
            for photo in report_photo_data_list
        ]

        session.add_all(photos)

        try:
            await session.commit()
            for photo in photos:
                await session.refresh(photo)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to add report photos: {str(e)}")

        return photos

    @classmethod
    async def delete_report_photo(cls, photo_id: int, session: AsyncSession) -> bool | None:
        query = select(ReportPhoto_db).filter_by(id=photo_id)
        result = await session.execute(query)
        photo = result.scalar_one_or_none()

        if photo is None:
            return None

        await session.delete(photo)

        try:
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to delete Report Photo: {str(e)}")
