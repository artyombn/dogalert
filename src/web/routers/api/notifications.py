import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.notification import Notification as Notification_schema
from src.schemas.notification import NotificationCreate
from src.services.notification_service import NotificationServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/notifications",
    tags=["API Notifications"],
)

@router.post(
    "/create",
    summary="Notification creation",
    response_model=Notification_schema,
)
async def create_notification(
        notification_data: NotificationCreate,
        session: AsyncSession = Depends(get_async_session),

) -> Notification_schema:
    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        sender_task = tg.create_task(
            UserServices.find_one_or_none_by_user_id(
                notification_data.sender_id, session,
            ),
        )
        report_task = tg.create_task(
            ReportServices.find_one_or_none_by_id(
                notification_data.report_id, session,
            ),
        )
        recipients_task = [
            tg.create_task(UserServices.find_one_or_none_by_user_id(recipient_id, session))
            for recipient_id in notification_data.recipient_ids
        ]

    sender = sender_task.result()
    report = report_task.result()
    recipients = [task.result() for task in recipients_task]
    logger.info(f"SENDER = {sender},\n"
                f"REPORT = {report},\n"
                f"RECIPIENTS = {recipients}")

    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    recipients_filtered = list(filter(None, recipients))
    recipients_filtered_ids = [user.id for user in recipients_filtered]
    recipients_set_ids = set(recipients_filtered_ids)
    recipients_filtered_ids = list(recipients_set_ids)

    logger.info(f"recipients_filtered = {recipients_filtered_ids}")

    if sender.id != report.user_id:
        raise HTTPException(status_code=404, detail="Report not belong to Sender")

    notification_filtered = NotificationCreate(
        method=notification_data.method,
        message=notification_data.message,
        recipient_ids=recipients_filtered_ids,
        sender_id=notification_data.sender_id,
        report_id=notification_data.report_id,
    )
    new_notification = await NotificationServices.create_notification(
        notification_filtered,
        session,
    )
    return Notification_schema.model_validate(new_notification)
