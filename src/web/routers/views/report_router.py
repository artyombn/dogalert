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
from src.database.models.geo import GeoFilterType
from src.schemas import ReportCreate, ReportPhotoCreate, ReportUpdate
from src.schemas.geo import GeolocationNearest
from src.schemas.notification import NotificationCreate, NotificationMethod
from src.services.geo_service import GeoServices
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

    async with asyncio.TaskGroup() as tg:
        user_db_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        pet_list_tasks = tg.create_task(UserServices.get_all_user_pets(user_id, session))

    user_db = user_db_task.result()
    pet_list = pet_list_tasks.result()

    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})


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
        reported_pet_task = tg.create_task(PetServices.find_one_or_none_by_id(
            pet_id=pet_id,
            session=session,
        ))
        user_geo_task = tg.create_task(UserServices.get_user_geolocation(user_id, session))

    user = user_task.result()
    reported_pet = reported_pet_task.result()
    user_geo = user_geo_task.result()

    if not user:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    if not reported_pet:
        return JSONResponse(
            content={"status": "error", "message": "Питомец не найден"},
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

    if user_geo:
        if user_geo.filter_type == GeoFilterType.REGION:

            recipients_telegram_ids = await GeoServices.find_all_telegram_uids_by_city(
                geo_data=user_geo,
                session=session,
            )
        elif user_geo.filter_type == GeoFilterType.RADIUS:

            user_geo_nearest_by_radius = GeolocationNearest(
                home_location=user_geo.home_location,
                radius=user_geo.radius,
            )

            recipients_telegram_ids = await GeoServices.find_all_telegram_uids_within_radius(
                geo_data=user_geo_nearest_by_radius,
                session=session,
            )
        elif user_geo.filter_type == GeoFilterType.POLYGON:
            recipients_telegram_ids = [237716145, 237716145, 237716145, 237716145, 237716145]
        else:
            logger.error("No filter type")
            return JSONResponse(
                content={"status": "error", "message": "Некорректная настройка уведомлений"},
                status_code=404,
            )
    else:
        return JSONResponse(
            content={"status": "error", "message": "Отсутствует геолокация"},
            status_code=404,
        )

    notification_schema = NotificationCreate(
        method=NotificationMethod.TELEGRAM_CHAT,
        message=notification_content(report_created, reported_pet),
        recipient_ids=recipients_telegram_ids,
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
        "photo_url": telegram_user.photo_url,
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


@router.patch("/update_report_info/{report_id}", response_model=None, include_in_schema=True)
async def update_report_info(
        request: Request,
        report_id: int,
        title: str | None = Form(None, example=None),
        content: str | None = Form(None, example=None),
        photos: list[UploadFile] | None = File(None, example=None),
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return JSONResponse(
            content={
                "status": "error",
                "message": "Пользователь не найден",
            },
            status_code=404,
        )

    user_id = int(user_id_str)

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        report_task = tg.create_task(ReportServices.find_one_or_none_by_id(report_id, session))

    user = user_task.result()
    report = report_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )
    if report is None:
        return JSONResponse(
            content={"status": "error", "message": "Объявление не найдено"},
            status_code=400,
        )

    if user.id != report.user.id:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь владельцем данного объявления"},
            status_code=400,
        )

    if photos:
        bot = request.app.state.bot
        aiohttp_session = request.app.state.aiohttp_session

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
            except Exception as e:
                logger.error(f"Ошибка отправки группы фото: {str(e)}")
                return JSONResponse(
                    content={"status": "error", "message": f"Ошибка отправки в Telegram: {str(e)}"},
                    status_code=500,
                )

            for msg in sent_msgs:
                if msg.photo:
                    file_ids.append(msg.photo[-1].file_id)
                else:
                    continue
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
            except Exception as e:
                logger.error(f"Ошибка отправки фото: {str(e)}")
                return JSONResponse(
                    content={
                        "status": "error",
                        "message": "Ошибка отправки фото. Попробуйте снова",
                    },
                    status_code=500,
                )
            if sent.photo:
                file_ids.append(sent.photo[-1].file_id)
            else:
                file_ids.append("")

        logger.info(f"Успешно отправлено {len(file_ids)} фото, file_ids: {file_ids}")

        report_photo_urls = []
        for file_id in file_ids:
            url = await get_file_url_by_file_id(file_id, aiohttp_session)
            if not url:
                continue
            report_photo_urls.append(url)

        report_photo_schemas = [ReportPhotoCreate(url=url) for url in report_photo_urls]
    else:
        report_photo_schemas = None

    update_data: dict[str, str | int] = {}
    if title is not None:
        update_data["title"] = str(title)
    if content is not None:
        update_data["content"] = str(content)

    report_update_schema = ReportUpdate(**update_data)  # type: ignore[arg-type]

    try:
        report_updated = await ReportServices.update_report(
            report_id=report.id,
            report_data=report_update_schema,
            session=session,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка при обновлении {e}"},
            status_code=500,
        )

    if report_updated:
        if report_photo_schemas:
            try:
                await ReportPhotoServices.create_many_report_photos(
                    report_id=report.id,
                    report_photo_data_list=report_photo_schemas,
                    session=session,
                )
            except Exception as e:
                logger.error(f"Report Photo creating error = {e}")
                return JSONResponse(
                    content={"status": "error", "message": "Ошибка при добавлении фотографий"},
                    status_code=500,
                )
    else:
        logger.error("Report wasn't updated")
        return JSONResponse(
            content={
                "status": "error",
                "message": "Данные объявления не были обновлены. Попробуйте снова",
            },
            status_code=500,
        )

    return JSONResponse(
        content={
            "status": "success",
            "redirect_url": f"/reports/{report_updated.id}",
        },
        status_code=200,
    )


@router.delete("/photo_delete/{photo_id}", response_model=None, include_in_schema=True)
async def delete_report_photo(
        request: Request,
        report_id: int,
        photo_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)

    if user_id_str is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    user_id = int(user_id_str)

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        report_task = tg.create_task(ReportServices.find_one_or_none_by_id(report_id, session))
        report_photos_task = tg.create_task(
            ReportPhotoServices.get_all_report_photos(report_id, session),
        )

    user = user_task.result()
    report = report_task.result()
    report_photos = report_photos_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    if report is None or report_photos is None:
        return JSONResponse(
            content={"status": "error", "message": "Объявление не найдено"},
            status_code=404,
        )

    if user.id != report.user.id:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь создателем объявления"},
            status_code=404,
        )

    if photo_id not in [report_photo.id for report_photo in report_photos]:
        return JSONResponse(
            content={"status": "error", "message": "Фото не найдено"},
            status_code=404,
        )

    await ReportPhotoServices.delete_report_photo(photo_id, session)
    return JSONResponse(
        content={"status": "success", "message": "Фото удалено"},
        status_code=200,
    )


@router.get("/update_report/{report_id}", response_class=HTMLResponse, include_in_schema=True)
async def show_update_report_page(
        request: Request,
        report_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if user_id_str is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    user = await UserServices.find_one_or_none_by_user_id(user_id, session)
    if user is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    async with asyncio.TaskGroup() as tg:
        report_task = tg.create_task(ReportServices.find_one_or_none_by_id(report_id, session))
        report_photos_task = tg.create_task(
            ReportPhotoServices.get_all_report_photos(report_id, session),
        )

    report = report_task.result()
    report_photos = report_photos_task.result()

    if report is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if user.id != report.user.id:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    return templates.TemplateResponse("report/update_report.html", {
        "request": request,
        "report": report,
        "report_photos": report_photos,
    })

@router.delete("/delete/{report_id}", response_model=None, include_in_schema=True)
async def delete_report(
        request: Request,
        report_id: int,
        session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    user_id_str = get_user_id_from_cookie(request)

    if user_id_str is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    user_id = int(user_id_str)

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        report_task = tg.create_task(ReportServices.find_one_or_none_by_id(report_id, session))

    user = user_task.result()
    report = report_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    if report is None:
        return JSONResponse(
            content={"status": "error", "message": "Объявление не найдено"},
            status_code=404,
        )

    if user.id != report.user.id:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь создателем объявления"},
            status_code=404,
        )

    await ReportServices.delete_report(report_id, session)
    return JSONResponse(
        content={"status": "success", "message": "Объявление удалено"},
        status_code=200,
    )

@router.get("/{id}", response_class=HTMLResponse, include_in_schema=True)
async def show_report_page(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_id = int(user_id_str)

    from sqlalchemy import select

    await session.execute(select(1))

    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(UserServices.find_one_or_none_by_user_id(user_id, session))
        user_reports_task = tg.create_task(UserServices.get_all_user_reports(user_id, session))
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

    user = user_task.result()
    user_reports = user_reports_task.result()
    report = report_task.result()
    report_photos = report_photos_task.result()

    if user is None or user_reports is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    if report is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if report_photos is None:
        logger.error("Report is not found")
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    user_reports_ids = [report.id for report in user_reports]

    if report.id in user_reports_ids:
        is_owner = True
    else:
        is_owner = False

    return templates.TemplateResponse("report/page.html", {
        "request": request,
        "report": report,
        "pet": report.pet,
        "report_photos": report_photos,
        "auth_required": False,
        "is_owner": is_owner,
    })
