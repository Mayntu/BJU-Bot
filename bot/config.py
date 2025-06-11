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

# TODO: Использовать pydantic для валидации настроек


# ------------------- Переменные окружения ------------------- #

BOT_TOKEN : str = os.getenv("BOT_TOKEN")
BOT_TELEGRAM_URL : str = os.getenv("BOT_TELEGRAM_URL")
OPENAI_KEY : str = os.getenv("OPENAI_KEY")
IMGBB_API_KEY : str = os.getenv("IMGBB_API_KEY")
DB_URL : str = os.getenv("DATABASE_URL")
REDIS_HOST : str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT : int = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
YOOKASSA_SHOP_ID : str = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY : str = os.getenv("YOOKASSA_SECRET_KEY")
RECEIPT_EMAIL : str = os.getenv("RECEIPT_EMAIL")

MAX_IMAGE_TOKENS : str = int(os.getenv("MAX_IMAGE_TOKENS", 1000))
MAX_DESCRIPTION_TOKENS : int = int(os.getenv("MAX_DESCRIPTION_TOKENS", 300))
FREE_MEAL_COUNT : int = int(os.getenv("FREE_MEAL_COUNT", 5))
OFERTA_FILE_ID : str = os.getenv("OFERTA_FILE_ID")

LOCALE : str = os.getenv("LOCALE", "ru_RU")


# ------------------- Варианты подписок ------------------- #

class SubscriptionsStore(Enum):
    """
    Enum для хранения тарифов подписок.
    Каждый тариф содержит название, цену и длительность в месяцах.
    """
    BASIC_ONE_DAY = ("basic", 1, 1)
    BASIC_ONE_MONTH = ("basic", 270, 1)
    BASIC_THREE_MONTH = ("basic", 770, 3)
    BASIC_SIX_MONTH = ("basic", 1490, 6)

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
    
    @staticmethod
    def get_by_duration(duration : int) -> "SubscriptionsStore":
        """
        Получает объект подписки по длительности.
        
        :param duration: Длительность подписки (int)
        :return: Объект SubscriptionsStore или None, если не найдено
        """
        for subscription in SubscriptionsStore:
            if str(subscription.duration_month) == str(duration):
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


class YOOKASSA_PAYMENT_STATUS(Enum):
    """
    Enum для хранения статусов платежей в ЮKassa.
    """
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"

    @staticmethod
    def is_successful(status: str) -> bool:
        """
        Проверяет, является ли статус успешным.
        
        :param status: Статус платежа
        :return: True, если статус успешный, иначе False
        """
        return status in [YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value]


# ------------------- Конфиг Tortoise ORM ------------------- #

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


# ------------------- Сообщения бота ------------------- #

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

BOT_DAILY_MEAL_REPORT : str = """📊 Статистика за {date}:

Калории: {total_calories} ккал
Ваша цель: {goal} ккал
{status}: {status_ccal} ккал

Белки: {total_proteins} г ({proteins_pct}%)
Жиры: {total_fats} г ({fats_pct}%)
Углеводы: {total_carbs} г ({carbs_pct}%)
Клетчатка: {total_fiber} г\n
🍽 Приемы пищи:
"""

BUY_TEXT : str = """🛒 Вы выбрали подписку на {duration} мес.
💳 Нажмите "Оплатить", а после успешного платежа — "Проверить".
⚠️ Прежде чем оплачивать, ознакомьтесь с пользовательским соглашением.
"""

HELLO_TEXT : str = """
<b>Добро пожаловать в Тарелку — твой ИИ-помошник по подсчету калорий в Telegram!</b>

Я анализирую еду по фото, голосу и тексту.

<b>Что я умею:</b>
📷 <b>Анализ фото еды</b> — ИИ распознает даже сложные и смешанные блюда.
🎤 <b>Голосовой и текстовый ввод еды</b> — говори или пиши, что съел, а я всё учту.
🍎 <b>Расчет КБЖУ и К</b> — калории, белки, жиры, углеводы и клетчатка с точностью до 90%.
📊 <b>Умный дневник</b> — я веду общую статистику за день и учитываю "цель" по калориям.

Чтобы начать, просто отправь фото еды, голосовое или текст — и я моментально всё посчитаю!
"""

HELP_TEXT : str = """
<b>Помощь по боту Тарелка</b>

<b>Тарелка</b> 🥣 – это ИИ-ассистент, который анализирует КБЖУ еды по фото, голосу или тексту. 

Как это работает:
• Отправьте <b>фото еды</b> 📷 в чат – бот распознает блюдо, проанализирует и выдаст КБЖУ-отчет.
• Напишите <b>текстовое</b> 🖊️ описание ("кофе с молоком") – бот выдаст КБЖУ-отчет. Желательно указывать примерный вес, можно давать пояснения, например "чайная ложка масла" или "хлеб бездрожжевой из ржаной муки".
• Отправьте <b>голосовое</b> 🎤сообщение ("омлет 200 грамм" или "омлет из одного яйца и молока») – бот расшифрует аудио и проанализирует.

После подсчета КБЖУ и вывода отчета можно откорректировать вес или состав блюда, нажав кнопку «Изменить» ✏️.  Например, написать "Вместо масла творожный сыр". Бот пересчитает КБЖУ и выведет обновленный отчет.
Можно полностью удалить прием пищи из суточной статистики, нажав кнопку <b>«Удалить» ❌</b>.
<b>Статистика калорийности за день</b> 📊 считается автоматически и находится в меню бота по команде /stats. 
Можно установить <b>«Цель» 🎯</b> по калорийности на день по команде <b>/set_goal</b> Она будет учитываться в статистике за день и показывать «перебор/недобор» по калориям

Команды в меню:
- <b>/start  →</b> Начать.
- <b>/stats →</b> Личная статистика по калориям за день.
- <b>/set_goal →</b> Выставить цель калорий на день.
- <b>/subscribe →</b> выбрать тарифный план.
- <b>/help →</b> Инструкции.

Еще больше информации и лайфхаков на канале @tarelka_kanal
По техническим вопросам пишите в личные сообщения @tarelka_kanal
"""

SET_GOAL_TEXT : str = "Введите желаемую дневную калорийность"

SUBSCRIBE_TEXT : str = """
Оформите подписку, чтобы продолжить пользоваться сервисом. 

💳 Выберите срок подписки:
"""

FREE_MEAL_END_MESSAGE : str = "К сожалению, бесплатные запросы закончились! Оформите подписку /subscribe"

SUBSCRIPTION_NOT_ACTIVE_MESSAGE : str = "❌ Подписка не активна. Пожалуйста, оплатите подписку. /subscribe"
