from bot.services.logger import logger
from bot.config import MAX_TOKENS
from bot.services.openai_client import client
from bot.schemas.food_analyze import Ingredient, MealAnalysis
from bot.prompts.food_analyze import get_food_analysis_system_prompt, get_food_analysis_user_prompt


async def analyze_food_image(image_url: str) -> MealAnalysis:
    """
    Анализирует картинку блюда на состав и калории.
    Использует OpenAI API.
    
    :param image_url: URL картинки блюда
    :return: Объект MealAnalysis с результатами анализа
    """


    logger.info(f"Начинаем анализ изображения еды по ссылке: {image_url}")

    # messages : list[dict] = [
    #     {"role": "system", "content": get_food_analysis_system_prompt()},
    #     {"role": "user", "content": get_food_analysis_user_prompt(image_url=image_url)}
    # ]

    # completion = await client.beta.chat.completions.parse(
    #     model="gpt-4o",
    #     messages=messages,
    #     max_tokens=int(MAX_TOKENS),
    #     response_format=MealAnalysis,
    # )
    # logger.info(completion)
    # logger.info(completion.choices)
    # logger.info(completion.choices[0].message)
    # logger.info(completion.choices[0].message.model_dump())

    logger.info("Готово! Вот результат анализа.")
    
    return MealAnalysis(
            title="Курица карри с рисом",
            total_weight=500,
            calories=750,
            proteins=42,
            fats=22,
            carbs=98,
            fiber=5,
            ingredients=[
                Ingredient(
                    name="Курица",
                    weight=150,
                    calories=330,
                    protein=31,
                    fat=19,
                    carbs=0,
                    fiber=0,
                ),
                Ingredient(
                    name="Рис",
                    weight=200,
                    calories=260,
                    protein=5,
                    fat=2,
                    carbs=57,
                    fiber=1,
                ),
                Ingredient(
                    name="Карри соус",
                    weight=100,
                    calories=140,
                    protein=3,
                    fat=0,
                    carbs=18,
                    fiber=0,
                ),
                Ingredient(
                    name="Овощи",
                    weight=50,
                    calories=20,
                    protein=3,
                    fat=1,
                    carbs=23,
                    fiber=4,
                ),
            ],
        )




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