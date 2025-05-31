import asyncio
import logging

from aiogram.types import BufferedInputFile, InputMediaPhoto, Message
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db_session import get_async_session
from src.schemas.pet import PetCreate, PetPhotoCreate, PetUpdate
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

@router.get("/profile/{id}", response_class=HTMLResponse, include_in_schema=True)
async def show_pet_profile(
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
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(
            pet_id=id,
            session=session,
        ))
        pet_photos_task = tg.create_task(PetPhotoServices.get_all_pet_photos(
            pet_id=id,
            session=session,
        ))

    user = user_task.result()
    pet = pet_task.result()
    pet_photos = pet_photos_task.result()

    if not user:
        return templates.TemplateResponse("no_telegram_login.html", {"request": request})

    if pet is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user_id in pet_owners_ids:
        is_owner = True
    else:
        is_owner = False

    formatted_pet = {
        "id": pet.id,
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
        "is_owner": is_owner,
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

    try:
        new_pet_schema = PetCreate(
            name=pet_name,
            breed=pet_breed,
            age=pet_age,
            color=pet_color,
            description=pet_description,
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
            content={"status": "error", "message": "Ошибка при создании питомца. Попробуйте снова"},
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
                content={"status": "error", "message": "Ошибка отправки фото. Попробуйте снова"},
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

    # pet_photo_urls = await asyncio.gather(
    #     *[get_file_url_by_file_id(file_id, aiohttp_session) for file_id in file_ids]
    # )
    pet_photo_urls = []
    for file_id in file_ids:
        url = await get_file_url_by_file_id(file_id, aiohttp_session)
        if not url:
            continue
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
            "redirect_url": f"/pets/profile/{pet_created.id}",
        },
        status_code=200,
    )

@router.patch("/update_pet_info/{pet_id}", response_model=None, include_in_schema=True)
async def update_pet_info(
        request: Request,
        pet_id: int,
        name: str | None = Form(None, example=None),
        breed: str | None = Form(None, example=None),
        age: int | None = Form(None, example=None),
        color: str | None = Form(None, example=None),
        description: str | None = Form(None, example=None),
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
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))

    user = user_task.result()
    pet = pet_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=400,
        )
    if pet is None:
        return JSONResponse(
            content={"status": "error", "message": "Питомец не найден"},
            status_code=400,
        )

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user.id not in pet_owners_ids:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь владельцем питомца"},
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

        pet_photo_urls = []
        for file_id in file_ids:
            url = await get_file_url_by_file_id(file_id, aiohttp_session)
            if not url:
                continue
            pet_photo_urls.append(url)

        pet_photo_schemas = [PetPhotoCreate(url=url) for url in pet_photo_urls]
    else:
        pet_photo_schemas = None

    update_data: dict[str, str | int] = {}
    if name is not None:
        update_data["name"] = str(name)
    if breed is not None:
        update_data["breed"] = str(breed)
    if age is not None:
        if isinstance(age, str):
            age = int(age)
        update_data["age"] = age
    if color is not None:
        update_data["color"] = str(color)
    if description is not None:
        update_data["description"] = str(description)

    pet_update_schema = PetUpdate(**update_data)  # type: ignore[arg-type]

    try:
        pet_updated = await PetServices.update_pet(
            pet_id=pet_id,
            pet_data=pet_update_schema,
            session=session,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Ошибка при обновлении {e}"},
            status_code=500,
        )

    if pet_updated:
        if pet_photo_schemas:
            try:
                await PetPhotoServices.create_many_pet_photos(
                    pet_id=pet_id,
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
        logger.error("Pet wasn't updated")
        return JSONResponse(
            content={
                "status": "error",
                "message": "Данные питомца не были обновлены. Попробуйте снова",
            },
            status_code=500,
        )

    return JSONResponse(
        content={
            "status": "success",
            "redirect_url": f"/pets/profile/{pet_updated.id}",
        },
        status_code=200,
    )

@router.delete("/photo_delete/{photo_id}", response_model=None, include_in_schema=True)
async def delete_pet_photo(
        request: Request,
        pet_id: int,
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
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))
        pet_photos_task = tg.create_task(PetPhotoServices.get_all_pet_photos(pet_id, session))

    user = user_task.result()
    pet = pet_task.result()
    pet_photos = pet_photos_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    if pet is None:
        return JSONResponse(
            content={"status": "error", "message": "Питомец не найден"},
            status_code=404,
        )

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user.id not in pet_owners_ids:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь владельцем питомца"},
            status_code=404,
        )

    if photo_id not in [pet_photo.id for pet_photo in pet_photos]:
        return JSONResponse(
            content={"status": "error", "message": "Фото не найдено"},
            status_code=404,
        )

    await PetPhotoServices.delete_pet_photo(photo_id, session)
    return JSONResponse(
        content={"status": "success", "message": "Фото удалено"},
        status_code=200,
    )


@router.get("/update_pet/{pet_id}", response_class=HTMLResponse, include_in_schema=True)
async def show_update_pet_page(
        request: Request,
        pet_id: int,
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
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))
        pet_photos_task = tg.create_task(PetPhotoServices.get_all_pet_photos(pet_id, session))

    pet = pet_task.result()
    pet_photos = pet_photos_task.result()

    if pet is None:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user.id not in pet_owners_ids:
        return templates.TemplateResponse("something_goes_wrong.html", {"request": request})

    return templates.TemplateResponse("pet/update_pet.html", {
        "request": request,
        "pet": pet,
        "pet_photos": pet_photos,
    })



@router.delete("/delete/{pet_id}", response_model=None, include_in_schema=True)
async def delete_pet(
        request: Request,
        pet_id: int,
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
        pet_task = tg.create_task(PetServices.find_one_or_none_by_id(pet_id, session))

    user = user_task.result()
    pet = pet_task.result()

    if user is None:
        return JSONResponse(
            content={"status": "error", "message": "Пользователь не найден"},
            status_code=404,
        )

    if pet is None:
        return JSONResponse(
            content={"status": "error", "message": "Питомец не найден"},
            status_code=404,
        )

    pet_owners_ids = [owner.id for owner in pet.owners]
    if user.id not in pet_owners_ids:
        return JSONResponse(
            content={"status": "error", "message": "Вы не являетесь владельцем питомца"},
            status_code=404,
        )

    await PetServices.delete_pet(pet_id, session)
    return JSONResponse(
        content={"status": "success", "message": "Питомец удален"},
        status_code=200,
    )


