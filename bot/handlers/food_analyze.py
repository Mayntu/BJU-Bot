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
    delete_food,
    get_daily_stats
)
from bot.services.logger import logger
from bot.keyboards.food_analyze import get_meal_action_keyboard
from bot.schemas.food_analyze import MealAnalysisResult
from bot.states.food_analyze import FoodAnalyzeState
from bot.middlewares.payments import SubscriptionMiddleware


router : Router = Router()
router.message.middleware(SubscriptionMiddleware())


# ------------------- FSM States ------------------- #

# Обработка редактирования блюда текстом
@router.message(FoodAnalyzeState.editing, F.text)
async def handle_edit_text(message : Message, state : FSMContext):
    state_data : dict = await state.get_data()
    meal_id : str = state_data.get("meal_id")
    prev_report_message_id = state_data.get("prev_report_message_id")
    wait_for_edit_message_id : int = state_data.get("wait_for_edit_message_id")
    
    new_meal_description : str = message.text
    
    result : MealAnalysisResult = await analyze_edit_food_text(meal_id=meal_id, description=new_meal_description)

    if not result.is_food:
        await message.answer(text="❗ Описание не относится к еде, пожалуйста, проверьте введённые данные", parse_mode="HTML")
    
    text : str = result.report
    meal_id : str = result.meal_id
    reply_markup = None
    if meal_id:
        reply_markup = get_meal_action_keyboard(meal_id=meal_id)
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)

    try:
        # await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_report_message_id)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=wait_for_edit_message_id)
        # await message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    await state.clear()


# Обработка редактирования блюда войсом
@router.message(FoodAnalyzeState.editing, F.voice)
async def handle_edit_voice(message : Message, state : FSMContext):
    state_data : dict = await state.get_data()
    meal_id : str = state_data.get("meal_id")

    prev_report_message_id = state_data.get("prev_report_message_id")
    wait_for_edit_message_id : int = state_data.get("wait_for_edit_message_id")

    voice = message.voice
    voice_file = await message.bot.get_file(voice.file_id)
    file_path : str = voice_file.file_path

    voice_file_url : str = f"https://api.telegram.org/file/bot{message.bot.token}/{file_path}"
    
    result : MealAnalysisResult = await analyze_edit_food_voice(meal_id=meal_id, file_url=voice_file_url)
    
    if not result.is_food:
        await message.answer(text="❗ Описание не относится к еде, пожалуйста, проверьте введённые данные", parse_mode="HTML")
    
    text : str = result.report
    meal_id : str = result.meal_id
    reply_markup = None
    if meal_id:
        reply_markup = get_meal_action_keyboard(meal_id=meal_id)
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)

    try:
        # await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_report_message_id)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=wait_for_edit_message_id)
        # await message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")
    
    await state.clear()



# ------------------- Callbacks ------------------- #

# Обработка нажатия кнопки редактирования блюда
@router.callback_query(F.data.startswith("edit:"))
async def meal_edit_callback(callback_query : CallbackQuery, state : FSMContext):
    meal_id : str = callback_query.data.split(":")[1]
    await state.set_state(FoodAnalyzeState.editing)
    await state.update_data(meal_id=meal_id, prev_report_message_id=callback_query.message.message_id)
    wait_for_edit_message = await callback_query.message.answer(
        text="✏️ Введите исправления для блюда (текстовое/голосовое сообщение):"
    )
    await state.update_data(wait_for_edit_message_id=wait_for_edit_message.message_id)
    await callback_query.message.delete_reply_markup()
    await callback_query.answer()


@router.callback_query(F.data.startswith("delete:"))
async def meal_delete_callback(callback_query : CallbackQuery, state : FSMContext):
    meal_id : str = callback_query.data.split(":")[1]
    await callback_query.message.delete_reply_markup()
    await delete_food(meal_id=meal_id)
    await callback_query.answer()
    await state.clear()



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
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None, False)
        logger.error(f"Ошибка при анализе фото: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id
    reply_markup = None
    if meal_id:
        reply_markup = get_meal_action_keyboard(meal_id=meal_id)
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)


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
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None, False)
        logger.error(f"Ошибка при анализе текста: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id
    reply_markup = None
    if meal_id:
        reply_markup = get_meal_action_keyboard(meal_id=meal_id)
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)


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
        result : MealAnalysisResult = MealAnalysisResult(f"❗ Возникла ошибка при попытке распознования", None, False)
        logger.error(f"Ошибка при анализе голоса: {e}")
    
    text : str = result.report
    meal_id : str = result.meal_id
    reply_markup = None
    if meal_id:
        reply_markup = get_meal_action_keyboard(meal_id=meal_id)
    
    await message.answer(text=text, parse_mode="HTML", reply_markup=reply_markup)
