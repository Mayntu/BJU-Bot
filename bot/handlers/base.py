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

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    # TODO: получить статистику из бд
    await message.answer(
        "📊 Статистика за сегодня:\n"
        "Калории: x ккал\n"
        "Белки: x г (x%)\n"
        "Жиры: x г (x%)\n"
        "Углеводы: x г (x%)\n"
        "Клетчатка: x г\n\n"
        "🍽 Приемы пищи:\n"
        "1. Омлет с овощами – x ккал\n"
        "2. Курица с рисом – x ккал"
    )
