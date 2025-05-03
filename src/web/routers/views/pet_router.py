import logging

from aiogram.types import InputMediaPhoto, Message, BufferedInputFile
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.pet import PetCreate, PetPhotoCreate
from src.services.pet_photo_service import PetPhotoServices
from src.services.pet_service import PetServices
from src.services.user_service import UserServices
from src.web.dependencies.get_data_from_cookie import get_user_id_from_cookie

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="src/web/templates")
router = APIRouter(
    prefix="/pets",
    tags=["Pets"],
)

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
        "user": user_db,
    })

@router.post("/create_with_photos")
async def upload_photos(
        request: Request,
        pet_name: str = Form(...),
        pet_breed: str = Form(...),
        pet_age: int = Form(...),
        pet_color: str = Form(...),
        pet_description: str = Form(...),
        photos: list[UploadFile] = File(...),
        session: AsyncSession = Depends(get_async_session),
):
    bot = request.app.state.bot

    user_id_str = get_user_id_from_cookie(request)
    if not user_id_str:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    user = await UserServices.find_one_or_none_by_user_id(int(user_id_str), session)

    logger.info(f"Получен запрос на загрузку {len(photos)} фото от пользователя {user_id_str}")

    if not user:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    if not photos:
        raise HTTPException(400, "Нет файлов для загрузки")

    for photo in photos:
        if photo.size > 50 * 1024 * 1024:  # 50 MB
            raise HTTPException(status_code=400, detail="Файл слишком большой")

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
            raise HTTPException(status_code=500, detail=f"Ошибка отправки в Telegram: {str(e)}")

        for msg in sent_msgs:
            file_ids.append(msg.photo[-1].file_id)
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
            raise HTTPException(status_code=500, detail=f"Ошибка отправки в Telegram: {str(e)}")
        file_ids.append(sent.photo[-1].file_id)
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
    pet_photo_schemas = []
    for file_id in file_ids:
        new_pet_photo_schema = PetPhotoCreate(
            url=file_id,
        )
        pet_photo_schemas.append(new_pet_photo_schema)

    try:
        pet_created = await PetServices.create_pet(
            owner_id=int(user_id_str),
            pet_data=new_pet_schema,
            session=session,
        )
    except Exception as e:
        logger.error(f"Pet creation error = {e}")
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    try:
        pet_photo_created = await PetPhotoServices.create_many_pet_photos(
            pet_id=pet_created.id,
            pet_photo_data_list=pet_photo_schemas,
            session=session,
        )
    except Exception as e:
        logger.error(f"Pet Photo creating error = {e}")
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    logger.info(f"Pet created = {pet_created}")
    logger.info(f"Pet with id={pet_created.id} photos added = {pet_photo_created}")
    response = JSONResponse(
        content={"redirect_url": f"/pets/profile?id={pet_created.id}"},
        status_code=200,
    )
    return response
"""
Успешно отправлено 1 фото, 
file_ids: ['AgACAgIAAxkDAAM2aBVVnhPXEi7eCa9vdBD1Fcj9n7kAAr8TMhutVqlI6Do_7Z0Hqo8BAAMCAAN3AAM2BA'], 
pet_name: PROVERKA
"""
