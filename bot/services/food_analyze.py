from tempfile import NamedTemporaryFile

from bot.config import MAX_IMAGE_TOKENS, MAX_DESCRIPTION_TOKENS, BOT_MEAL_REPORT
from bot.services.logger import logger
from bot.services.openai_client import client
from bot.services.images_handler import get_image_bytes, upload_to_imgbb
from bot.services.voice_transcription import get_voice_path, transcribe_audio, close_voice_file
from db.models import User, Meal, Ingredient
from bot.schemas.food_analyze import IngredientAnalysis, MealAnalysis
from bot.prompts.food_analyze import get_food_analysis_system_prompt, get_food_analysis_user_prompt, get_food_analysis_by_description_system_prompt, get_food_analysis_by_description_user_prompt

import aiohttp


async def analyze_food_image(file_url : str, user_id : int) -> str:
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

    # Сохраняем анализ блюда в БД и формируем отчет
    result : str = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)

    return result


async def analyze_food_text(text : str, user_id : int) -> str:
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
    
    # Сохраняем анализ блюда в БД и формируем отчет
    result : str = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)
    return result


async def analyze_food_voice(file_url : str, user_id : int) -> str:
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
    meal_analysis : MealAnalysis = await get_meal_analysis(messages=messages, max_tokens=MAX_DESCRIPTION_TOKENS)
    
    # Сохраняем анализ блюда в БД и формируем отчет
    result : str = await save_meal_to_db_and_get_report(meal_analysis=meal_analysis, user_id=user_id)
    return result



async def get_meal_analysis(messages : list[dict], max_tokens : int, model : str = "gpt-4o") -> MealAnalysis:
    """
    Отправляет запрос к OpenAI API для анализа блюда.
    
    :param messages: Список сообщений для запроса
    :param max_tokens: Максимальное количество токенов для ответа
    :return: Объект MealAnalysis с результатами анализа
    """
    
    logger.info("="*50)
    logger.info("Начинаем анализ блюда...")
    logger.info(f"Используем модель: {model}")
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
        error_message : str = "Не удалось получить результат анализа. Проверьте входные данные."
        logger.error(error_message)
        raise ValueError(error_message)
    
    logger.info(completion.choices[0].message.model_dump())
    
    return completion.choices[0].message.parsed


async def save_meal_to_db_and_get_report(meal_analysis : MealAnalysis, user_id : int) -> str:
    """
    Сохраняет анализ блюда в БД и формирует отчет.
    
    :param meal_analysis: Объект MealAnalysis с результатами анализа
    :param user_id: ID пользователя, который отправил описание
    :return: Строка с отчетом о блюде
    """
    
    meal : Meal = Meal(
        user=await User.get(telegram_id=user_id),
        name=meal_analysis.title,
        total_weight=meal_analysis.total_weight,
        total_calories=meal_analysis.calories,
        total_protein=meal_analysis.proteins,
        total_fat=meal_analysis.fats,
        total_carbs=meal_analysis.carbs,
        total_fiber=meal_analysis.fiber,
    )
    await meal.save()

    result : str = BOT_MEAL_REPORT.format(
        meal_name=meal.name,
        meal_weight=meal.total_weight,
        meal_ccal=meal.total_calories,
        meal_protein=meal.total_protein,
        meal_fat=meal.total_fat,
        meal_carb=meal.total_carbs,
        meal_fiber=meal.total_fiber,
    )

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
        result += f"\n[{ingredient.name}] - {ingredient.weight} гр. | {ingredient.calories} ккал | Белки {ingredient.protein} гр. | Жиры {ingredient.fat} гр. | Углеводы {ingredient.carbs} гр. | Клетчатка {ingredient.fiber} гр;\n"
    
    logger.info(f"Для пользователя {user_id} было проанализировано блюдо: {meal.name} и сохранено в БД.")
    logger.info("="*50)
    return result
