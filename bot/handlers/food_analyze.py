from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from bot.services.food_analyze import (
    analyze_food_image,
    analyze_food_text,
    analyze_food_voice,
    analyze_edit_food_text,
    analyze_edit_food_voice,
    get_daily_stats
)
from bot.services.logger import logger
from bot.keyboards.food_analyze import get_meal_action_keyboard
from bot.schemas.food_analyze import MealAnalysisResult
from bot.states.food_analyze import FoodAnalyzeState


router : Router = Router()



# ------------------- FSM States ------------------- #

# Обработка редактирования блюда текстом
@router.message(FoodAnalyzeState.editing, F.text)
async def handle_edit_text(message : Message, state : FSMContext):
    state_data : dict = await state.get_data()
    meal_id : str = state_data.get("meal_id")
    
    new_meal_description : str = message.text
    
    result : MealAnalysisResult = await analyze_edit_food_text(meal_id=meal_id, description=new_meal_description)
    
    text : str = result.report
    meal_id : str = result.meal_id
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=get_meal_action_keyboard(meal_id=meal_id))
    
    await state.clear()


# Обработка редактирования блюда войсом
@router.message(FoodAnalyzeState.editing, F.voice)
async def handle_edit_voice(message : Message, state : FSMContext):
    state_data : dict = await state.get_data()
    meal_id : str = state_data.get("meal_id")

    voice = message.voice
    voice_file = await message.bot.get_file(voice.file_id)
    file_path : str = voice_file.file_path

    voice_file_url : str = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    
    result : MealAnalysisResult = await analyze_edit_food_voice(meal_id=meal_id, file_url=voice_file_url)
    
    text : str = result.report
    meal_id : str = result.meal_id
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=get_meal_action_keyboard(meal_id=meal_id))
    
    await state.clear()



# ------------------- Callbacks ------------------- #

# Обработка нажатия кнопки редактирования блюда
@router.callback_query(F.data.startswith("edit:"))
async def meal_edit_callback(callback_query : CallbackQuery, state : FSMContext):
    meal_id : str = callback_query.data.split(":")[1]
    await state.set_state(FoodAnalyzeState.editing)
    await state.update_data(meal_id=meal_id)
    await callback_query.message.answer(
        text="✏️ Введите исправления для блюда (текстовое/голосовое сообщение):"
    )
    await callback_query.answer()



# ------------------- Commands ------------------- #

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    # TODO: получить статистику из бд
    result : str = await get_daily_stats(user_id=message.from_user.id)
    await message.answer(text=result, parse_mode="HTML")



# ------------------- Handlers ------------------- #

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
        result : MealAnalysisResult = await analyze_food_image(file_url=photo_url, user_id=message.from_user.id)
    except Exception as e:
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None)
        logger.error(f"Ошибка при анализе фото: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id

    await message.answer(text=text, parse_mode="HTML", reply_markup=get_meal_action_keyboard(meal_id=meal_id))


# Обработка текстовых сообщений
@router.message(F.text)
async def handle_text(message : Message):
    await message.answer(
        text="📝 Определю состав и калории блюда. Пожалуйста, подождите..."
    )
    
    try:
        result : MealAnalysisResult = await analyze_food_text(
            text=message.text,
            user_id=message.from_user.id
        )
    except Exception as e:
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None)
        logger.error(f"Ошибка при анализе текста: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=get_meal_action_keyboard(meal_id=meal_id))


# Обработка голосовых сообщений
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
        result : MealAnalysisResult = await analyze_food_voice(
            file_url=voice_file_url,
            user_id=message.from_user.id
        )
    except Exception as e:
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None)
        logger.error(f"Ошибка при анализе голоса: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=get_meal_action_keyboard(meal_id=meal_id))
