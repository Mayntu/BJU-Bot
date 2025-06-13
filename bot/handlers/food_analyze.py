from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from datetime import date

from db.models import User
from bot.services.food_analyze import (
    analyze_food_image,
    analyze_food_text,
    analyze_food_voice,
    analyze_edit_food_text,
    analyze_edit_food_voice,
    delete_food,
    get_daily_stats,
    get_available_report_dates,
)
from bot.services.user import set_calories_goal, get_user_local_date, get_user
from bot.services.logger import logger
from bot.keyboards.food_analyze import get_meal_action_keyboard, build_stats_navigation_kb
from bot.keyboards.menu import get_timezone_offset_keyboard
from bot.schemas.food_analyze import MealAnalysisResult
from bot.states.food_analyze import FoodAnalyzeState
from bot.states.user import GoalState, TimezoneState
from bot.config import SET_GOAL_TEXT
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


@router.message(GoalState.waiting_for_goal)
async def process_goal_input(message: Message, state: FSMContext):
    goal : str = message.text.strip()
    try:
        await set_calories_goal(user_id=message.from_user.id, goal=goal)
    except ValueError as e:
        await message.answer(str(e))
        return
    
    await message.answer(f"Ваша цель сохранена: {goal} ккал в день ✅")
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


@router.callback_query(F.data.startswith("stats:"))
async def callback_stats_navigation(callback_query: CallbackQuery, state: FSMContext):
    user_id : int = callback_query.from_user.id
    target_date = date.fromisoformat(callback_query.data.split(":")[1])
    
    min_date, max_date = await get_available_report_dates(user_id=user_id)
    today = await get_user_local_date(user_id=user_id)

    logger.info(f"min_date : {min_date} | max_date : {max_date}")
    logger.info(f"target_date : {target_date}")

    if target_date < min_date or target_date > today:
        await callback_query.answer("Нет данных за эту дату", show_alert=True)
        return

    result : str = await get_daily_stats(user_id=user_id, date=target_date)
    kb = build_stats_navigation_kb(target_date, min_date, today)

    await callback_query.message.edit_text(result, reply_markup=kb, parse_mode="HTML")
    await callback_query.answer()



# ------------------- Commands ------------------- #

@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext):
    user_id : int = message.from_user.id
    user : User = await get_user(user_id=user_id)
    if not user.timezone_setted:  # если ещё не установлен tz
        await state.set_state(TimezoneState.waiting_for_offset)
        await state.update_data(show_stats_after_tz=True)
        await message.answer(
            "👋 Добро пожаловать!\n\nПрежде чем начать, выберите ваш часовой пояс:",
            reply_markup=get_timezone_offset_keyboard()
        )
        return
    
    await show_stats(user_id=user_id, chat_id=message.chat.id, bot=message.bot)


async def show_stats(user_id: int, chat_id: int, bot: Bot):
    date_for_stats = await get_user_local_date(user_id=user_id)
    min_date, _ = await get_available_report_dates(user_id=user_id)
    result = await get_daily_stats(user_id=user_id, date=date_for_stats)
    kb = build_stats_navigation_kb(date_for_stats, min_date, date_for_stats)

    await bot.send_message(chat_id=chat_id, text=result, reply_markup=kb, parse_mode="HTML")


@router.message(Command("set_goal"))
async def cmd_calories_goal(message: Message, state: FSMContext):
    await message.answer(
        text=SET_GOAL_TEXT,
    )
    await state.set_state(GoalState.waiting_for_goal)



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
