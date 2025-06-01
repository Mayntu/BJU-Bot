from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services.user import create_user_if_not_exists
from bot.keyboards.menu import get_main_menu

router : Router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await create_user_if_not_exists(
        user_id=message.from_user.id,
        username=message.from_user.username or "Unknown"
    )
    await message.answer(
        "<b>Добро пожаловать!</b>\n\n"
        "Я помогу тебе следить за питанием. Просто пришли фото, голос или текст с описанием еды.",
        reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 Команды:\n"
        "/start – начать\n"
        "/help – помощь\n"
        "/stats – статистика за день\n\n"
        "📸 Отправь фото еды или опиши голосом – я определю состав и калории."
    )
