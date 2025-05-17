import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Notification as Notification_db
from src.schemas.notification import NotificationCreate

logger = logging.getLogger(__name__)


class NotificationServices:
    @classmethod
    async def create_notification(
            cls,
            notif_data: NotificationCreate,
            session: AsyncSession,
    ) -> Notification_db:
        db_notif = Notification_db(**notif_data.model_dump(exclude_unset=True))
        session.add(db_notif)

        try:
            await session.commit()
            await session.refresh(db_notif)
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to create notification: {str(e)}")

        return db_notif

    @classmethod
    async def find_one_or_none_by_id(
            cls,
            notif_id: int,
            session: AsyncSession,
    ) -> Notification_db | None:
        query = select(Notification_db).filter_by(id=notif_id)
        result = await session.execute(query)

        return result.scalar_one_or_none()
