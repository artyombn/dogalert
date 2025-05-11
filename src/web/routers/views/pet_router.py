import asyncio
import logging

from aiogram.types import BufferedInputFile, InputMediaPhoto, Message
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.pet import PetCreate, PetPhotoCreate
from src.services.pet_photo_service import PetPhotoServices
from src.services.pet_service import PetServices
from src.services.user_service import UserServices
from src.web.dependencies.date_format import format_russian_date
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie
from src.web.dependencies.photo_from_telegram import get_file_url_by_file_id

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/pets",
    tags=["Pets"],
)

@router.get("/profile", response_class=HTMLResponse, include_in_schema=True)
async def show_pet_profile(
        request: Request,
        id: int,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)

    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    tasks = [
        PetServices.find_one_or_none_by_id(
            pet_id=id,
            session=session,
        ),
        PetPhotoServices.get_all_pet_photos(
            pet_id=id,
            session=session,
        ),
    ]

    pet, pet_photos = await asyncio.gather(*tasks)

    if pet is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if pet_photos is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    formatted_pet = {
        "name": pet.name,
        "breed": pet.breed,
        "age": pet.age,
        "color": pet.color,
        "description": pet.description,
        "last_vaccination": format_russian_date(pet.last_vaccination),
        "next_vaccination": format_russian_date(pet.next_vaccination),
        "last_parasite_treatment": format_russian_date(pet.last_parasite_treatment),
        "next_parasite_treatment": format_russian_date(pet.next_parasite_treatment),
        "last_fleas_ticks_treatment": format_russian_date(pet.last_fleas_ticks_treatment),
        "next_fleas_ticks_treatment": format_russian_date(pet.next_fleas_ticks_treatment),
    }

    return templates.TemplateResponse("pet/profile.html", {
        "request": request,
        "pet": formatted_pet,
        "pet_photos": pet_photos,
    })

@router.get("/add_pet", response_class=HTMLResponse, include_in_schema=True)
async def add_new_pet(
        request: Request,
        session: AsyncSession = Depends(get_async_session),
) -> HTMLResponse:
    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user_db = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if user_db is None:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    return templates.TemplateResponse("pet/new_pet.html", {
        "request": request,
    })

@router.post("/create_with_photos")
async def create_pet_with_photos(
        request: Request,
        pet_name: str = Form(...),
        pet_breed: str = Form(...),
        pet_age: int = Form(...),
        pet_color: str = Form(...),
        pet_description: str = Form(...),
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

    user = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)
    if not user:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
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
                content={"status": "error", "message": f"Ошибка отправки в Telegram: {str(e)}"},
                status_code=500,
            )
        if sent.photo:
            file_ids.append(sent.photo[-1].file_id)
        else:
            file_ids.append("")

    logger.info(f"Успешно отправлено {len(file_ids)} фото, file_ids: {file_ids}")
    logger.info(f"Данные питомца:\n"
                f"Имя = {pet_name}\n"
                f"Порода = {pet_breed}\n"
                f"Возраст = {pet_age}\n"
                f"Цвет = {pet_color}\n"
                f"Особенности = {pet_description}")
    new_pet_schema = PetCreate(
        name=pet_name,
        breed=pet_breed,
        age=pet_age,
        color=pet_color,
        description=pet_description,
    )

    # pet_photo_urls = await asyncio.gather(
    #     *[get_file_url_by_file_id(file_id, aiohttp_session) for file_id in file_ids]
    # )
    pet_photo_urls = []
    for file_id in file_ids:
        url = await get_file_url_by_file_id(file_id, aiohttp_session)
        pet_photo_urls.append(url)

    pet_photo_schemas = [PetPhotoCreate(url=url) for url in pet_photo_urls]

    try:
        pet_created = await PetServices.create_pet(
            owner_id=int(user_id_str),
            pet_data=new_pet_schema,
            session=session,
        )
    except Exception as e:
        logger.error(f"Pet creation error = {e}")
        return JSONResponse(
            content={"status": "error", "message": "Ошибка при создании питомца"},
            status_code=500,
        )
    if pet_created:
        try:
            pet_photo_created = await PetPhotoServices.create_many_pet_photos(
                pet_id=pet_created.id,
                pet_photo_data_list=pet_photo_schemas,
                session=session,
            )
        except Exception as e:
            logger.error(f"Pet Photo creating error = {e}")
            return JSONResponse(
                content={"status": "error", "message": "Ошибка при добавлении фотографий"},
                status_code=500,
            )
    else:
        logger.error("Pet wasn't created")
        return JSONResponse(
            content={"status": "error", "message": "Питомец не был создан"},
            status_code=500,
        )

    logger.info(f"Pet created = {pet_created}")
    logger.info(f"Pet with id={pet_created.id} photos added = {pet_photo_created}")
    return JSONResponse(
        content={
            "status": "success",
            "redirect_url": f"/pets/profile?id={pet_created.id}",
        },
        status_code=200,
    )
