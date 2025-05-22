import asyncio
import json
import logging
from urllib.parse import urlencode

from aiogram.types import BufferedInputFile, InputMediaPhoto, Message
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.broker.producer import send_task_to_rabbitmq
from src.config.config import settings
from src.database.db_session import get_async_session
from src.schemas import ReportCreate, ReportPhotoCreate
from src.schemas.notification import NotificationCreate, NotificationMethod
from src.services.notification_service import NotificationServices
from src.services.pet_service import PetServices
from src.services.report_photo_service import ReportPhotoServices
from src.services.report_service import ReportServices
from src.services.user_service import UserServices
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie
from src.web.dependencies.notification_content_handles import notification_content
from src.web.dependencies.photo_from_telegram import get_file_url_by_file_id
from src.web.dependencies.telegram_user_data import TelegramUser

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

@router.get("/create_report", response_class=HTMLResponse, include_in_schema=True)
async def add_new_report(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user_db = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    pet_list = await UserServices.get_all_user_pets(user_id, session)

    return templates.TemplateResponse("report/new_report.html", {
        "request": request,
        "pet_list": pet_list,
    })

@router.post("/create_with_photos")
async def create_report_with_photos(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    pet_id: int = Form(...),
    photos: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    bot = request.app.state.bot
    aiohttp_session = request.app.state.aiohttp_session

    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не авторизован"},
            status_code=401,
        )

    user_id = int(user_id_str)

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        report_pet_task = tg.create_task(PetServices.find_one_or_none_by_id(
            pet_id=pet_id,
            session=session,
        ))

    user = user_task.result()
    report_pet = report_pet_task.result()

    if not user:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    try:
        new_report_schema = ReportCreate(
            title=title,
            content=content,
        )

        report_created = await ReportServices.create_report(
            report_data=new_report_schema,
            user_id=user_id,
            pet_id=pet_id,
            session=session,
        )
        if report_created is None:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "У этого питомца уже есть активное объявление!",
                },
                status_code=400,
            )
    except ValidationError as e:
        logger.error(f"ValidationError = {e}")
        return JSONResponse(
            content={"status": "error", "message": "Ошибка валидации. Проверьте введенные поля"},
            status_code=422,
        )
    except Exception as e:
        logger.error(f"Report creation error = {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": "Ошибка при создании объявления. Попробуйте снова",
            },
            status_code=500,
        )

    logger.info(f"Получен запрос на загрузку {len(photos)} фото от пользователя {user_id_str}")

    if not photos:
        return JSONResponse(
            content={"status": "error", "message": "Необходимо загрузить хотя бы одно фото"},
            status_code=400,
        )

    for photo in photos:
        file_size = photo.size or 0
        if file_size > 50 * 1024 * 1024:  # 50 MB
            return JSONResponse(
                content={"status": "error", "message": "Файл слишком большой"},
                status_code=400,
            )

    file_ids: list[str] = []

    if len(photos) > 1:
        media = []
        for photo in photos:
            data = await photo.read()  # bytes
            input_file = BufferedInputFile(data, photo.filename or "photo.jpg")
            media.append(InputMediaPhoto(media=input_file))
        try:
            sent_msgs: list[Message] = await bot.send_media_group(
                chat_id=user.telegram_id,
                media=media,
            )
            for msg in sent_msgs:
                await bot.delete_message(chat_id=user.telegram_id, message_id=msg.message_id)

            for msg in sent_msgs:
                if msg.photo:
                    file_ids.append(msg.photo[-1].file_id)
                else:
                    file_ids.append("")

        except Exception as e:
            logger.error(f"Ошибка отправки группы фото: {str(e)}")
            return JSONResponse(
                content={"status": "error", "message": f"Ошибка отправки в Telegram: {str(e)}"},
                status_code=500,
            )
    else:
        photo = photos[0]
        data = await photo.read()
        input_file = BufferedInputFile(data, photo.filename or "photo.jpg")
        try:
            sent: Message = await bot.send_photo(
                chat_id=user.telegram_id,
                photo=input_file,
            )
            await bot.delete_message(chat_id=user.telegram_id, message_id=sent.message_id)
            if sent.photo:
                file_ids.append(sent.photo[-1].file_id)
            else:
                file_ids.append("")
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {str(e)}")
            return JSONResponse(
                content={"status": "error", "message": "Ошибка отправки фото. Попробуйте снова"},
                status_code=500,
            )

    logger.info(f"Успешно отправлено {len(file_ids)} фото, file_ids: {file_ids}")
    logger.info(f"Данные объявления:\n"
                f"Заголовок = {title}\n"
                f"Текст = {content}\n")

    report_photo_urls = []
    for file_id in file_ids:
        url = await get_file_url_by_file_id(file_id, aiohttp_session)
        if not url:
            continue
        report_photo_urls.append(url)

    report_photo_schemas = [ReportPhotoCreate(url=url) for url in report_photo_urls]

    try:
        report_photo_created = await ReportPhotoServices.create_many_report_photos(
            report_id=report_created.id,
            report_photo_data_list=report_photo_schemas,
            session=session,
        )
    except Exception as e:
        logger.error(f"Report Photo creating error = {e}")
        return JSONResponse(
            content={"status": "error", "message": "Ошибка при добавлении фотографий"},
            status_code=500,
        )

    logger.info(f"Report created = {report_created.__dict__}")
    logger.info(f"Report with id={report_created.id} photos added = {report_photo_created}")

    notification_schema = NotificationCreate(
        method=NotificationMethod.TELEGRAM_CHAT,
        message=notification_content(report_created, report_pet),
        recipient_ids=[237716145, 237716145, 237716145, 237716145, 237716145],
        sender_id=user_id,
        report_id=report_created.id,
    )
    report_notification = await NotificationServices.create_notification(
        notif_data=notification_schema,
        session=session,
    )

    logger.info(f"-- REPORT NOTIF = {report_notification.__dict__}")

    report_url = f"{settings.MAIN_DOMEN}/reports/{report_created.id}"
    logger.info(f"REPORT URL = {report_url}")
    await send_task_to_rabbitmq(report_notification, report_url)

    return JSONResponse(
        content={
            "status": "success",
            "redirect_url": f"/reports/{report_created.id}",
        },
        status_code=200,
    )

@router.post("/auth")
async def user_auth_from_report_url_inline(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    data = await request.json()
    init_data = data.get("initData")
    report_id = data.get("reportId")

    logger.info(f"Received REPORT initData: {init_data}")

    if not init_data:
        logger.warning("initData not found. Returning JSON redirect.")
        return JSONResponse(
            status_code=200,
            content={"redirect_url": "/no_telegram_login"},
        )

    telegram_user = TelegramUser.from_init_data(init_data)
    if not telegram_user:
        logger.warning("telegram_user not found. Returning JSON redirect.")
        return JSONResponse(
            status_code=200,
            content={"redirect_url": "/no_telegram_login"},
        )

    user_db = await UserServices.find_one_or_none_by_tgid(telegram_user.id, session)
    if not user_db:
        logger.info(f"INIT_DATA AUTH = {init_data}")
        return JSONResponse(
            status_code = 200,
            content={"redirect_url": f"/agreement?{urlencode({'initData': init_data})}"},
    )

    response = JSONResponse(
        status_code = 200,
        content={"redirect_url": f"/reports/{report_id}"},
    )

    cookie_data = json.dumps({
        "user_id": str(user_db.id),
        "photo_url": telegram_user.photo_url
    })

    response.set_cookie(
        key="user_data",
        value=cookie_data,
        httponly=True,
        secure=True,
        max_age=3600 * 24 * 1,
    )
    logger.info(f"COOKIE SET = {cookie_data}")
    return response

@router.get("/{id}", response_class=HTMLResponse, include_in_schema=True)
async def show_report_page(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        logger.info("No user_id in cookie need to auth")
        return templates.TemplateResponse("report/page.html", {
            "request": request,
            "report": {"id": id},
            "auth_required": True
        })

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        report_task = tg.create_task(
            ReportServices.find_one_or_none_by_id(
                report_id=id,
                session=session,
            ),
        )
        report_photos_task = tg.create_task(
            ReportPhotoServices.get_all_report_photos(
                report_id=id,
                session=session,
            ),
        )

    report = report_task.result()
    report_photos = report_photos_task.result()

    if report is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if report_photos is None:
        logger.error("Report is not found")
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    return templates.TemplateResponse("report/page.html", {
        "request": request,
        "report": report,
        "report_photos": report_photos,
        "auth_required": False
    })
