import os

from dotenv import load_dotenv
from enum import Enum

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
YOOKASSA_SHOP_ID : str = os.getenv("YOOKAASSA_SHOP_ID")
YOOKASSA_SECRET_KEY : str = os.getenv("YOOKASSA_SECRET_KEY")


class SubscriptionsStore(Enum):
    BASIC = ("basic", 1500, 1)
    PRO = ("pro", 3500, 1)

    @staticmethod
    def get_by_title(title: str) -> "SubscriptionsStore":
        """
        Получает объект подписки по названию.
        
        :param title: Название подписки
        :return: Объект SubscriptionsStore или None, если не найдено
        """
        for subscription in SubscriptionsStore:
            if subscription.title == title:
                return subscription
        
        return None

    def __init__(self, title : str, price : float, duration_month : int) -> None:
        self.title = title
        self.price = price
        self.duration_month = duration_month
    
    # @staticmethod
    # def find_by_duration(duration_month : int) -> "ScriptStore":
    #     for script in SubscriptionsStore:
    #         if duration_month == script.duration_month:
    #             return script
        
    #     return None


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

BUY_TEXT : str = """🛒 Вы выбрали подписку {title}.
💳 Нажмите "Оплатить", а после успешного платежа — "Проверить".
⚠️ Прежде чем оплачивать, ознакомьтесь с пользовательским соглашением.
"""

HELLO_TEXT : str = """
<b>Добро пожаловать в Тарелка — твой ИИ-помошник по подсчету калорий в Telegram!</b>

Просто отправь фото еды, голосовое или текст — и я моментально разберу состав, калории и БЖУ. 
<b>Что я умею:</b>
✅ <b>Анализ фото еды</b> — ИИ распознает даже сложные блюда.
✅ <b>Голосовой и текстовый ввод</b> — говори или пиши, что съел, а я всё учту.
✅ <b>Расчет КБЖУ и К</b> — калории, белки, жиры, углеводы и клетчатка с точностью до 90%.
✅ <b>Умный дневник</b> — статистика за день.
Чтобы начать, просто отправь мне фото своего завтрака, обеда или ужина — и я всё посчитаю!
"""

HELP_TEXT : str = """
<b>Помощь по боту Tarelka</b>
<b>Тарелка</b> – это ИИ-ассистент, который анализирует еду по фото, голосу или тексту. 
<b>Как это работает:</b>
• Отправьте фото еды в чат – бот распознает блюдо и посчитает КБЖУ.
• Напишите текстовое описание ("кофе с молоком") – бот выдаст отчет.
• Отправьте голосовое сообщение ("омлет 200 грамм и апельсин") – бот расшифрует аудио и проанализирует.
После подсчета КБЖУ и вывода отчета можно откорректировать вес или состав блюда, нажав кнопку «Изменить».  Например, написать "Вместо масла творожный сыр". Бот пересчитает КБЖУ и выведет обновленный отчет.
Можно полностью удалить прием пищи из суточной статистики, нажав кнопку «Удалить».
Статистика калорийности за день находится в меню бота по команде /stats.

<b>Команды в меню:</b>
- <b>/start</b>  → Начать.
- <b>/help</b> → Инструкции.
- <b>/stats</b> → Личная статистика по калориям за день.
- <b>/subscribe</b> – выбрать тарифный план.
Еще больше информации и лайфхаков на канале: @tarelka_kanal   
Нужна помощь?
По техническим вопросам: @...
"""
