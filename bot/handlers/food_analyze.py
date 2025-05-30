from aiogram import Router, F
from aiogram.types import Message

from bot.services.food_analyze import analyze_food_image, analyze_food_text, analyze_food_voice
from bot.services.logger import logger


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

    try:
        result : str = await analyze_food_image(file_url=photo_url, user_id=message.from_user.id)
    except Exception as e:
        result = f"❗ Возникла ошибка при попытке распознования"
        logger.error(f"Ошибка при анализе фото: {e}")
    
    await message.answer(text=result, parse_mode="HTML")


@router.message(F.text)
async def handle_text(message : Message):
    await message.answer(
        text="📝 Определю состав и калории блюда. Пожалуйста, подождите..."
    )
    
    try:
        result : str = await analyze_food_text(
            text=message.text,
            user_id=message.from_user.id
        )
    except Exception as e:
        result = f"❗ Возникла ошибка при попытке распознования"
        logger.error(f"Ошибка при анализе текста: {e}")
    
    await message.answer(text=result, parse_mode="HTML")

@router.message(F.voice)
async def handle_voice(message : Message):
    await message.answer(
        text="🎤 Голосовое сообщение получено! Я определю состав и калории блюда. Пожалуйста, подождите..."
    )
    
    voice = message.voice
    voice_file = await message.bot.get_file(voice.file_id)
    file_path : str = voice_file.file_path

    voice_file_url : str = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"

    try:
        result : str = await analyze_food_voice(
            file_url=voice_file_url,
            user_id=message.from_user.id
        )
    except Exception as e:
        result = f"❗ Возникла ошибка при попытке распознования"
        logger.error(f"Ошибка при анализе голоса: {e}")
    
    await message.answer(text=result, parse_mode="HTML")
