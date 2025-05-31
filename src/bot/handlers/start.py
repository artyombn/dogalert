from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from src.config.config import settings

start_router = Router()

@start_router.message(CommandStart())
async def start_message(message: types.Message) -> None:
    photo_id = settings.START_MESSAGE_PHOTO_ID
    webapp_url = settings.MAIN_DOMEN

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=webapp_url),
                ),
            ],
        ],
    )

    if message.from_user:
        username = message.from_user.username
    else:
        await message.answer_photo(
            photo=photo_id,
            caption="Привет! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )

    try:
        await message.answer_photo(
            photo=photo_id,
            caption=f"Привет, @{username}!\n"
                    f"В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )
    except Exception:
        photo = FSInputFile("src/web/static/images/image.jpg")
        await message.answer_photo(
            photo=photo,
            caption=f"Привет, @{username}!\n"
                    f"В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )

@start_router.message()
async def any_message_handler(message: types.Message) -> None:
    photo_id = settings.START_MESSAGE_PHOTO_ID
    webapp_url = settings.MAIN_DOMEN

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=webapp_url),
                ),
            ],
        ],
    )

    if message.from_user:
        username = message.from_user.username
    else:
        await message.answer_photo(
            photo=photo_id,
            caption="Привет! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )

    try:
        await message.answer_photo(
            photo=photo_id,
            caption=f"Привет, @{username}!\n"
                    f"В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )
    except Exception:
        photo = FSInputFile("src/web/static/images/image.jpg")
        await message.answer_photo(
            photo=photo,
            caption=f"Привет, @{username}!\n"
                    f"В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )


