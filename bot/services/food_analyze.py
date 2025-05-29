from bot.services.logger import logger
from bot.config import MAX_TOKENS, BOT_MEAL_REPORT
from bot.services.openai_client import client
from bot.services.images_handler import upload_to_imgur
from db.models import User, Meal, Ingredient
from bot.schemas.food_analyze import IngredientAnalysis, MealAnalysis
from bot.prompts.food_analyze import get_food_analysis_system_prompt, get_food_analysis_user_prompt

import aiohttp


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

    logger.info(f"{int(MAX_TOKENS)} токенов будет использовано для ответа.")
    logger.info(f"{image_url} картинка будет проанализирована.")

    # Отправляем запрос к openai для анализа блюда
    completion = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=messages,
        max_tokens=int(MAX_TOKENS),
        response_format=MealAnalysis,
    )

    logger.info("Анализ завершен. Результат:")

    # Проверяем, что ответ содержит необходимые данные
    if not completion.choices or not completion.choices[0].message.parsed:
        logger.error("Не удалось получить результат анализа. Проверьте входные данные.")
        raise ValueError("Не удалось получить результат анализа. Проверьте входные данные.")
    
    logger.info(completion.choices[0].message.model_dump())
    
    return completion.choices[0].message.parsed


async def analyze_food_image(file_url : str, user_id : int) -> str:
    # TODO: Загрузка изображения из телеграма в публичный доступ (например, Imgur)

    # # Качаем байты изображения по file_url телеграма
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(file_url) as resp:
    #         if resp.status != 200:
    #             logger.error("Не удалось скачать изображение.")
    #             return
    #         image_bytes = await resp.read()

    # # Получаем публичную ссылку на изображение в Imgur
    # imgur_url = await upload_to_imgur(image_bytes=image_bytes)

    # Получаем анализ блюда с помощью OpenAI API
    food_result : MealAnalysis = await get_food_analysis(image_url="https://i.imgur.com/fzzXPVr.jpeg")

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

# async def analyze_food_img(url : str) -> str:
#     """
#     Анализирует картинку блюда на состав и калории.
#     Использует OpenAI API.
    
#     :param url: URL картинки блюда
#     :return: Результат анализа в виде строки
#     """

#     return "🍽️ Анализ завершен! Примерный состав блюда:\n" \
#            "Калории: 500 ккал\n" \
#            "Белки: 30 г\n" \
#            "Жиры: 20 г\n" \
#            "Углеводы: 50 г"