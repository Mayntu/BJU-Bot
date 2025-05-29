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
    await analyze_food_image(image_url="https://rice.ua/wp-content/uploads/2018/04/kurica_karri_s_risom.jpg")
    # photo = message.photo[-1]
    # photo_file = await message.bot.get_file(photo.file_id)
    # photo_url : str = f"https://api.telegram.org/file/bot{message.bot.token}/{photo_file.file_path}"

    # result = await analyze_food_img(url = photo_url)
    # await message.answer(text=result, parse_mode="HTML")
