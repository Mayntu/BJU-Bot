import pytz

from datetime import datetime, time
from openai import LengthFinishReasonError

from bot.config import MAX_IMAGE_TOKENS, MAX_DESCRIPTION_TOKENS, BOT_MEAL_REPORT, BOT_DAILY_MEAL_REPORT
from bot.services.logger import logger
from bot.services.openai_client import client
from bot.services.images_handler import get_image_bytes, upload_to_imgbb
from bot.services.voice_transcription import get_voice_path, transcribe_audio, close_voice_file
from db.models import User, Meal, Ingredient, UserDailyReport, UserDailyMeal
from bot.schemas.food_analyze import IngredientAnalysis, MealAnalysis, MealAnalysisResult
from bot.prompts.food_analyze import (
    get_food_analysis_system_prompt,
    get_food_analysis_user_prompt,
    get_food_analysis_by_description_system_prompt,
    get_food_analysis_by_description_user_prompt,
    edit_food_analysis_by_description_system_prompt,
    edit_food_analysis_by_description_user_prompt,
)


async def analyze_food_image(file_url : str, user_id : int) -> MealAnalysisResult:
    """
    Загружает картинку на сторонний сервис, использует openai для анализа блюда и сохраняет результат в БД.
    :param file_url: телеграм URL картинки блюда
    :param user_id: ID пользователя, который отправил картинку
    :return: Строка с результатом анализа блюда
    """


    # Качаем байты изображения по file_url телеграма
    image_bytes : bytes = await get_image_bytes(image_url=file_url)

    # Получаем публичную ссылку на изображение в Imgbb
    image_url = await upload_to_imgbb(image_bytes=image_bytes)

    # Контекст для запроса к OpenAI
    messages : list[dict] = [
        {
            "role": "system",
            "content": get_food_analysis_system_prompt(),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": get_food_analysis_user_prompt(),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]
        }
    ]
    
    # Получаем анализ блюда с помощью OpenAI API
    meal_analysis : MealAnalysis = await get_meal_analysis(messages=messages, max_tokens=MAX_IMAGE_TOKENS)

    if not meal_analysis.is_food:
        # если блюдо не еда, возвращаем результат с нулевыми значениями
        logger.info("Получено описание, которое не относится к еде. Возвращаем нулевые значения.")
        return MealAnalysisResult(
            report="❗ Описание не относится к еде, пожалуйста, проверьте введённые данные",
            meal_id=None,
            is_food=meal_analysis.is_food
        )

    # Сохраняем анализ блюда в БД и формируем отчет
    result : MealAnalysisResult = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)
    return result


async def analyze_food_text(text : str, user_id : int) -> MealAnalysisResult:
    """
    Анализирует описание блюда на состав и калории.
    Использует OpenAI API.
    
    :param text: текст описания блюда
    :param user_id: ID пользователя, который отправил описание
    :return: Строка с результатом анализа блюда
    """
    
    # Контекст для запроса к OpenAI
    messages : list[dict] = [
        {
            "role": "system",
            "content": get_food_analysis_by_description_system_prompt(),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": get_food_analysis_by_description_user_prompt(description=text),
                }
            ]
        }
    ]

    # Получаем анализ блюда с помощью OpenAI API
    meal_analysis : MealAnalysis = await get_meal_analysis(messages=messages, max_tokens=MAX_DESCRIPTION_TOKENS)

    if not meal_analysis.is_food:
        # если блюдо не еда, возвращаем результат с нулевыми значениями
        logger.info("Получено описание, которое не относится к еде. Возвращаем нулевые значения.")
        return MealAnalysisResult(
            report="❗ Описание не относится к еде, пожалуйста, проверьте введённые данные",
            meal_id=None,
            is_food=meal_analysis.is_food
        )
    
    # Сохраняем анализ блюда в БД и формируем отчет
    result : MealAnalysisResult = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)
    return result


async def analyze_food_voice(file_url : str, user_id : int) -> MealAnalysisResult:
    """
    Анализирует голосовое сообщение с описанием блюда.
    Использует OpenAI API для транскрипции и анализа.
    
    :param file_url: URL голосового сообщения
    :param user_id: ID пользователя, который отправил голосовое сообщение
    :return: Строка с результатом анализа блюда
    """

    # Получаем путь к аудиофайлу
    voice_path : str = await get_voice_path(file_url=file_url)

    # Транскрибируем аудиофайл с помощью whisper ai api
    transcribed_text : str = await transcribe_audio(file_path=voice_path)

    # Закрываем файл
    await close_voice_file(file_path=voice_path)
    
    # Контекст для запроса к OpenAI
    messages : list[dict] = [
        {
            "role": "system",
            "content": get_food_analysis_by_description_system_prompt(),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": get_food_analysis_by_description_user_prompt(description=transcribed_text),
                }
            ]
        }
    ]

    # Получаем анализ блюда с помощью OpenAI API
    meal_analysis : MealAnalysis = await get_meal_analysis(messages=messages, max_tokens=MAX_DESCRIPTION_TOKENS, growth_tokens=300)

    if not meal_analysis.is_food:
        # если блюдо не еда, возвращаем результат с нулевыми значениями
        logger.info("Получено описание, которое не относится к еде. Возвращаем нулевые значения.")
        return MealAnalysisResult(
            report="❗ Описание не относится к еде, пожалуйста, проверьте введённые данные",
            meal_id=None,
            is_food=meal_analysis.is_food
        )
    
    # Сохраняем анализ блюда в БД и формируем отчет
    result : MealAnalysisResult = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)
    return result


async def analyze_edit_food_text(meal_id : str, description : str) -> MealAnalysisResult:
    """
    Анализирует описание блюда на состав и калории, редактируя уже существующее блюдо.
    Использует OpenAI API.
    :param meal_id: ID блюда, которое нужно отредактировать
    :param description: корректировка описания блюда
    :return: MealAnalysisResult с отчетом о блюде
    """

    # Получаем оригинальное блюдо
    original_meal : Meal = await Meal.get(id=meal_id).prefetch_related("ingredients")

    # Создаём предыдущее описание блюда для контекста
    prev_description : str = BOT_MEAL_REPORT.format(
        meal_name=original_meal.name,
        meal_weight=original_meal.total_weight,
        meal_ccal=original_meal.total_calories,
        meal_protein=original_meal.total_protein,
        meal_fat=original_meal.total_fat,
        meal_carb=original_meal.total_carbs,
        meal_fiber=original_meal.total_fiber,
    )

    for ingredient in original_meal.ingredients:
        prev_description += f"\n{ingredient.name} - {ingredient.weight} гр. | {ingredient.calories} ккал | Белки {ingredient.protein} гр. | Жиры {ingredient.fat} гр. | Углеводы {ingredient.carbs} гр. | Клетчатка {ingredient.fiber} гр;\n"
    
    # Контекст для запроса к openai
    messages : list[dict] = [
        {
            "role": "system",
            "content": edit_food_analysis_by_description_system_prompt(),
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": edit_food_analysis_by_description_user_prompt(
                        prev_description=prev_description,
                        description=description
                    ),
                }
            ]
        }
    ]

    # Получаем новый анализ блюда через openai
    new_meal_analysis : MealAnalysis = await get_meal_analysis(messages=messages, max_tokens=MAX_DESCRIPTION_TOKENS)

    if not new_meal_analysis.is_food:
        # если блюдо не еда, возвращаем результат с нулевыми значениями
        logger.info("Получено описание, которое не относится к еде. Возвращаем нулевые значения.")
        return MealAnalysisResult(
            report=prev_description,
            meal_id=meal_id,
            is_food=new_meal_analysis.is_food
        )

    # Удаляем старые ингредиенты из бд
    await Ingredient.filter(meal=original_meal).delete()

    # Апдейтаем оригинальное блюдо
    original_meal.name = new_meal_analysis.title
    original_meal.total_weight = new_meal_analysis.total_weight
    original_meal.total_calories = new_meal_analysis.calories
    original_meal.total_protein = new_meal_analysis.proteins
    original_meal.total_fat = new_meal_analysis.fats
    original_meal.total_carbs = new_meal_analysis.carbs
    original_meal.total_fiber = new_meal_analysis.fiber

    await original_meal.save()

    # Формируем новый отчет о блюде
    new_report : str = BOT_MEAL_REPORT.format(
        meal_name=original_meal.name,
        meal_weight=original_meal.total_weight,
        meal_ccal=original_meal.total_calories,
        meal_protein=original_meal.total_protein,
        meal_fat=original_meal.total_fat,
        meal_carb=original_meal.total_carbs,
        meal_fiber=original_meal.total_fiber,
    )

    # Сохраняем новые ингредиенты в бд
    for ingredient in new_meal_analysis.ingredients:
        await Ingredient.create(
            meal=original_meal,
            name=ingredient.name,
            weight=ingredient.weight,
            calories=ingredient.calories,
            protein=ingredient.protein,
            fat=ingredient.fat,
            carbs=ingredient.carbs,
            fiber=ingredient.fiber
        )
        new_report += f"\n{ingredient.name} - {ingredient.weight} гр. | {ingredient.calories} ккал | Белки {ingredient.protein} гр. | Жиры {ingredient.fat} гр. | Углеводы {ingredient.carbs} гр. | Клетчатка {ingredient.fiber} гр;\n"

    return MealAnalysisResult(report=new_report, meal_id=meal_id, is_food=new_meal_analysis.is_food)


async def analyze_edit_food_voice(meal_id : str, file_url : str) -> MealAnalysisResult:
    """
    Анализирует голосовое сообщение с описанием блюда, редактируя уже существующее блюдо.
    Использует OpenAI API для транскрипции и анализа.
    
    :param meal_id: ID блюда, которое нужно отредактировать
    :param file_url: URL голосового сообщения
    :return: MealAnalysisResult с отчетом о блюде
    """

    # Получаем путь к аудиофайлу
    voice_path : str = await get_voice_path(file_url=file_url)

    # Транскрибируем аудиофайл с помощью whisper ai api
    transcribed_text : str = await transcribe_audio(file_path=voice_path)

    # Закрываем файл
    await close_voice_file(file_path=voice_path)
    
    # Возвращаем результат анализа блюда, используя функцию для анализа текста
    return await analyze_edit_food_text(meal_id=meal_id, description=transcribed_text)


async def delete_food(meal_id : str) -> str:
    """
    Удаляет блюдо из БД по ID.
    
    :param meal_id: ID блюда, которое нужно удалить
    :return: Строка с подтверждением удаления
    """
    logger.info(f"Удаляем блюдо с ID {meal_id} из БД...")
    
    meal : Meal = await Meal.get(id=meal_id)

    # Удаляем ингредиенты, связанные с этим блюдом
    await Ingredient.filter(meal=meal).delete()

    await meal.delete()

    logger.info(f"Блюдо с ID {meal_id} успешно удалено.")
    
    return f"✅ Блюдо '{meal.name}' успешно удалено из базы данных."


async def get_daily_stats(user_id : int) -> str:
    """
    Получает статистику по блюдам пользователя за сегодня.
    
    :param user_id: ID пользователя
    :return: Строка с отчетом о блюдах пользователя за сегодня
    """
    logger.info(f"Получаем статистику по блюдам пользователя {user_id} за сегодня...")

    user = await User.get(id=user_id)
    user_tz = pytz.timezone(user.timezone)
    logger.info(f"Таймзона пользователя: {user.timezone}")

    # Получаем текущую дату в таймзоне пользователя
    local_date = datetime.now(user_tz).date()

    report = await UserDailyReport.get_or_none(
        user_id=user.id,
        date=local_date
    )

    meals = await UserDailyMeal.filter(
        user_id=user.id,
        date=local_date
    ).order_by("order")

    if not report:
        return "📊 Статистика за сегодня пока недоступна."

    total_calories = report.total_calories or 1
    protein_pct = round((report.total_protein * 4 / total_calories) * 100)
    fat_pct = round((report.total_fat * 9 / total_calories) * 100)
    carbs_pct = round((report.total_carbs * 4 / total_calories) * 100)

    meals_text = "\n".join(
        [f"{idx + 1}. {meal.name} – {int(meal.calories)} ккал" for idx, meal in enumerate(meals)]
    ) or "Нет приёмов пищи на сегодня."

    def format_float(value : float, digits : int = 1):
        # Округляем, а если после округления .0, убираем
        formatted = f"{value:.{digits}f}"
        if formatted.endswith(".0"):
            return formatted[:-2]
        return formatted

    result : str = BOT_DAILY_MEAL_REPORT.format(
        total_calories=format_float(report.total_calories, 0),
        total_proteins=format_float(report.total_protein),
        total_fats=format_float(report.total_fat),
        total_carbs=format_float(report.total_carbs),
        total_fiber=format_float(report.total_fiber),
        proteins_pct=protein_pct,
        fats_pct=fat_pct,
        carbs_pct=carbs_pct
    )
    result += meals_text
    
    logger.info(f"Статистика для пользователя {user_id} получена.")
    logger.info("="*50)

    return result



async def get_meal_analysis(messages : list[dict], max_tokens : int, model : str = "gpt-4o", retries : int = 2, growth_tokens : int = 200) -> MealAnalysis:
    """
    Отправляет запрос к OpenAI API для анализа блюда.
    
    :param messages: Список сообщений для запроса
    :param max_tokens: Максимальное количество токенов для ответа
    :param model: Модель OpenAI для использования
    :param retries: Количество попыток запроса в случае ошибки
    :param growth_tokens: Количество токенов, на которое будет увеличиваться max_tokens при повторных попытках
    :return: Объект MealAnalysis с результатами анализа
    """
    # TODO: Сделать проверку на превышение лимита токенов openai
    
    logger.info("="*50)
    logger.info("Начинаем анализ блюда...")
    logger.info(f"Используем модель: {model}")

    attempt : int = 0

    # Пытаемся получить ответ от openai с увеличением лимита токенов при необходимости
    while attempt < retries:
        try:
            logger.info(f"{max_tokens} токенов будет использовано для ответа.")
            
            # Отправляем запрос к openai для анализа блюда
            completion = await client.beta.chat.completions.parse(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                response_format=MealAnalysis,
            )
        
            logger.info("Анализ завершен. Результат:")
            
            # Проверяем, что ответ содержит необходимые данные
            if not completion.choices or not completion.choices[0].message.parsed:
                error_message : str = "Ответ пустой или не разобран."
                logger.error(error_message)
                raise ValueError(error_message)
        
            logger.info(completion.choices[0].message.model_dump())
            
            return completion.choices[0].message.parsed
        except LengthFinishReasonError as e:
            logger.warning(f"Достигнут лимит токенов: {max_tokens}, увеличиваем лимит на {growth_tokens} токенов и пробуем снова")
            max_tokens += growth_tokens
            attempt += 1
        except Exception as e:
            logger.error(f"Ошибка при анализе блюда: {e}")
    
    raise RuntimeError("Не удалось получить ответ от openai после нескольких попыток")



async def save_meal_to_db_and_get_report(meal_analysis : MealAnalysis, user_id : int) -> MealAnalysisResult:
    """
    Сохраняет анализ блюда в БД и формирует отчет.
    
    :param meal_analysis: Объект MealAnalysis с результатами анализа
    :param user_id: ID пользователя, который отправил описание
    :return: Строка с отчетом о блюде
    """
    logger.info(f"Сохраняем блюдо {meal_analysis.title} в БД для пользователя {user_id}...")
    
    meal : Meal = Meal(
        user=await User.get(id=user_id),
        name=meal_analysis.title,
        total_weight=meal_analysis.total_weight,
        total_calories=meal_analysis.calories,
        total_protein=meal_analysis.proteins,
        total_fat=meal_analysis.fats,
        total_carbs=meal_analysis.carbs,
        total_fiber=meal_analysis.fiber,
    )
    await meal.save()


    logger.info("Формируем отчет о блюде...")
    # Формируем отчет о блюде
    result : str = BOT_MEAL_REPORT.format(
        meal_name=meal.name,
        meal_weight=meal.total_weight,
        meal_ccal=meal.total_calories,
        meal_protein=meal.total_protein,
        meal_fat=meal.total_fat,
        meal_carb=meal.total_carbs,
        meal_fiber=meal.total_fiber,
    )

    # Сохраняем ингредиенты в бд и формируем отчет по каждому ингредиенту
    for ingredient in meal_analysis.ingredients:
        ingredient_model : Ingredient = Ingredient(
            meal=meal,
            name=ingredient.name,
            weight=ingredient.weight,
            calories=ingredient.calories,
            protein=ingredient.protein,
            fat=ingredient.fat,
            carbs=ingredient.carbs,
            fiber=ingredient.fiber,
        )
        await ingredient_model.save()
        result += f"\n{ingredient.name} - {ingredient.weight} гр. | {ingredient.calories} ккал | Белки {ingredient.protein} гр. | Жиры {ingredient.fat} гр. | Углеводы {ingredient.carbs} гр. | Клетчатка {ingredient.fiber} гр;\n"
    
    logger.info(f"Для пользователя {user_id} было проанализировано блюдо: {meal.name} и сохранено в БД.")
    logger.info("="*50)
    return MealAnalysisResult(report=result, meal_id=meal.id, is_food=meal_analysis.is_food)
