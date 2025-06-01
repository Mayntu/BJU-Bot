import os

from dotenv import load_dotenv

load_dotenv()

# from pydantic import BaseSettings

# class Settings(BaseSettings):
#     BOT_TOKEN: str
#     DATABASE_URL: str
#     OPENAI_KEY: str

#     class Config:
#         env_file = ".env"

# settings : Settings = Settings()


BOT_TOKEN : str = os.getenv("BOT_TOKEN")
OPENAI_KEY : str = os.getenv("OPENAI_KEY")
IMGBB_API_KEY : str = os.getenv("IMGBB_API_KEY")
DB_URL : str = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
MAX_IMAGE_TOKENS : str = int(os.getenv("MAX_IMAGE_TOKENS", 1000))
MAX_DESCRIPTION_TOKENS : int = int(os.getenv("MAX_DESCRIPTION_TOKENS", 300))

TORTOISE_ORM = {
    "connections": {
        "default": DB_URL
    },
    "apps": {
        "models": {
            "models": ["db.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}

BOT_MEAL_REPORT : str = """{meal_name}  
Вес блюда: {meal_weight} гр.  
Примерная калорийность: {meal_ccal} ккал.  

БЖУК:  
Белки: {meal_protein} гр.  
Жиры: {meal_fat} гр.  
Углеводы: {meal_carb} гр.  
Клетчатка: {meal_fiber} гр.  

Состав:
"""

BOT_DAILY_MEAL_REPORT : str = """📊 Статистика за сегодня:
Калории: {total_calories} ккал
Белки: {total_proteins} г ({proteins_pct}%)
Жиры: {total_fats} г ({fats_pct}%)
Углеводы: {total_carbs} г ({carbs_pct}%)
Клетчатка: {total_fiber} г\n
🍽 Приемы пищи:
"""
