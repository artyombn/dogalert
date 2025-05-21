import asyncio
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.notification import NotificationCreate, NotificationCreateWithNoSender
from src.services.notification_service import NotificationServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

@router.post(
    "/create", response_model=None, include_in_schema=True)
async def create_notification(
        request: Request,
        notification_data: NotificationCreateWithNoSender,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)
    if user_id_str is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    user_id = int(user_id_str)
    sender = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if sender is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    async with asyncio.TaskGroup() as tg:
        report_task = tg.create_task(
            ReportServices.find_one_or_none_by_id(
                notification_data.report_id, session,
            ),
        )
        recipients_task = [
            tg.create_task(UserServices.find_one_or_none_by_tgid(tg_id, session))
            for tg_id in notification_data.recipient_ids
        ]

    report = report_task.result()
    recipients = [task.result() for task in recipients_task]
    logger.info(f"SENDER = {sender},\n"
                f"REPORT = {report},\n"
                f"RECIPIENTS = {recipients}")

    if report is None:
        return JSONResponse(
            content={"status": "error", "message": "Объявление не найдено"},
            status_code=404,
        )

    recipients_filtered = list(filter(None, recipients))
    recipients_filtered_ids = [user.telegram_id for user in recipients_filtered]
    recipients_set_ids = set(recipients_filtered_ids)
    recipients_filtered_ids = list(recipients_set_ids)

    logger.info(f"recipients_filtered = {recipients_filtered_ids}")

    if sender.id != report.user_id:
        return JSONResponse(
            content={"status": "error", "message": "Объявление не принадлежит отправителю"},
            status_code=404,
        )

    notification_filtered = NotificationCreate(
        method=notification_data.method,
        message=notification_data.message,
        recipient_ids=recipients_filtered_ids,
        sender_id=sender.id,
        report_id=notification_data.report_id,
    )
    new_notification = await NotificationServices.create_notification(
        notification_filtered,
        session,
    )
    logger.info(f"Notification set = {new_notification.__dict__}")

    return JSONResponse(
        content={"status": "success", "message": "Уведомления созданы и отправлены в обработку"},
        status_code=200,
    )
