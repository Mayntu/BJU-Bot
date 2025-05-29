from aiogram import Router, F
from aiogram.types import Message

from bot.services.food_analyze import analyze_food_image


router : Router = Router()

# Обработка картинок блюд
@router.message(F.photo)
async def handle_photo(message : Message):
    await message.answer(
        text="📸 Фото получено! Я определю состав и калории блюда. Пожалуйста, подождите..."
    )
    photo = message.photo[-1]
    photo_file = await message.bot.get_file(photo.file_id)
    photo_url : str = f"https://api.telegram.org/file/bot{message.bot.token}/{photo_file.file_path}"

    result : str = await analyze_food_image(file_url=photo_url, user_id=message.from_user.id)
    await message.answer(text=result, parse_mode="HTML")
