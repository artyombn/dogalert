from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

start_router = Router()

@start_router.message(CommandStart())
async def start_message(message: types.Message):
    username = message.from_user.username
    photo_id = "AgACAgIAAxkDAAMQaBI_Ig7_8_80HBXn31dFojKX7L8AAuTtMRv8mZlIFL4kxF3gZdIBAAMCAAN5AAM2BA"
    webapp_url = "https://merely-concise-macaw.ngrok-free.app"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ]
    )
    try:
        await message.answer_photo(
            photo=photo_id,
            caption=f"Привет, @{username}! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )
    except Exception:
        photo = FSInputFile("src/web/static/images/image.jpg")
        await message.answer_photo(
            photo=photo,
            caption=f"Привет, @{username}! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )

@start_router.message()
async def any_message_handler(message: types.Message):
    username = message.from_user.username
    photo_id = "AgACAgIAAxkDAAMQaBI_Ig7_8_80HBXn31dFojKX7L8AAuTtMRv8mZlIFL4kxF3gZdIBAAMCAAN5AAM2BA"
    webapp_url = "https://merely-concise-macaw.ngrok-free.app"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть приложение",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ]
    )
    try:
        await message.answer_photo(
            photo=photo_id,
            caption=f"Привет, @{username}! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )
    except Exception:
        photo = FSInputFile("src/web/static/images/image.jpg")
        await message.answer_photo(
            photo=photo,
            caption=f"Привет, @{username}! В этом боте ты можешь следить за пропавшими рядом питомцами",
            reply_markup=keyboard,
        )

