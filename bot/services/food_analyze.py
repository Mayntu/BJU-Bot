from bot.services.logger import logger
from bot.config import MAX_IMAGE_TOKENS, MAX_DESCRIPTION_TOKENS, BOT_MEAL_REPORT
from bot.services.openai_client import client
from bot.services.images_handler import get_image_bytes, upload_to_imgbb
from db.models import User, Meal, Ingredient
from bot.schemas.food_analyze import IngredientAnalysis, MealAnalysis
from bot.prompts.food_analyze import get_food_analysis_system_prompt, get_food_analysis_user_prompt, get_food_analysis_by_description_system_prompt, get_food_analysis_by_description_user_prompt


async def get_food_analysis(image_url: str) -> MealAnalysis:
    """
    Анализирует картинку блюда на состав и калории.
    Использует OpenAI API.
    
    :param image_url: URL картинки блюда
    :return: Объект MealAnalysis с результатами анализа
    """


    logger.info(f"Начинаем анализ изображения еды по ссылке: {image_url}")
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

    logger.info(f"{MAX_IMAGE_TOKENS} токенов будет использовано для ответа.")
    logger.info(f"{image_url} картинка будет проанализирована.")

    # Отправляем запрос к openai для анализа блюда
    completion = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=MAX_IMAGE_TOKENS,
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


async def analyze_food_image(file_url : str, user_id : int) -> str:
    """
    Загружает картинку на сторонний сервис, использует openai для анализа блюда и сохраняет результат в БД.
    :param file_url: телеграм URL картинки блюда
    :param user_id: ID пользователя, который отправил картинку
    :return: Строка с результатом анализа блюда
    """


    # Качаем байты изображения по file_url телеграма
    image_bytes : bytes = get_image_bytes(image_url=file_url)

    # Получаем публичную ссылку на изображение в Imgbb
    image_url = await upload_to_imgbb(image_bytes=image_bytes)

    # Получаем анализ блюда с помощью OpenAI API
    food_result : MealAnalysis = await get_food_analysis(image_url=image_url)

    meal : Meal = Meal(
        user=await User.get(telegram_id=user_id),
        name=food_result.title,
        total_weight=food_result.total_weight,
        total_calories=food_result.calories,
        total_protein=food_result.proteins,
        total_fat=food_result.fats,
        total_carbs=food_result.carbs,
        total_fiber=food_result.fiber,
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

    for ingredient in food_result.ingredients:
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
    return result



async def get_food_analysis_by_text(text : str) -> MealAnalysis:
    """
    Анализирует описание блюда на состав и калории.
    Использует OpenAI API.
    
    :param text: Описание картинки блюда
    :return: Объект MealAnalysis с результатами анализа
    """
    
    
    logger.info("Начинаем анализ блюда по тексту")
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
    logger.info(f"{MAX_DESCRIPTION_TOKENS} токенов будет использовано для ответа.")
    logger.info(f"{text} будет проанализирован.")

    # Отправляем запрос к openai для анализа блюда
    completion = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=MAX_DESCRIPTION_TOKENS,
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


async def analyze_food_text(text : str, user_id : int) -> str:
    """
    Анализирует описание блюда на состав и калории.
    Использует OpenAI API.
    
    :param text: текст описания блюда
    :param user_id: ID пользователя, который отправил описание
    :return: Строка с результатом анализа блюда
    """
    
    meal_analysis : MealAnalysis = await get_food_analysis_by_text(text = text)
    
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
    return result
