import pytz
import locale

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date, timedelta
from babel.dates import format_date



def get_meal_action_keyboard(meal_id : str) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с действиями для блюда.
    :param dish_id: ID блюда
    :return: InlineKeyboardMarkup с кнопками для редактирования и удаления блюда
    """
    return InlineKeyboardMarkup(inline_keyboard=[   
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{meal_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete:{meal_id}")],
    ])

def build_stats_navigation_kb(current_date: date, min_date: date, max_date: date, locale_str: str = "ru_RU") -> InlineKeyboardMarkup:
    """
    Создаёт кастомную клавиатуру для навигации по датам с учётом границ
    :param current_date: date текущая дата
    :param min_date: date минимальная дата
    :param max_date: date максимальная дата
    :param locale_str: Строка какой язык для форматирования месяца
    :return: InlineKeyboardMarkup с кнопками дат
    """
    buttons : list = []

    def format_day(d: date):
        """
        Форматирует дату под названия дня месяца

        :param d: Дата для форматирования
        :return: str Форматированный день месяца
        """
        return format_date(d, format="d MMMM", locale=locale_str)

    if current_date > min_date:
        prev_date = current_date - timedelta(days=1)
        buttons.append(InlineKeyboardButton(
            text=f"◀️ {format_day(prev_date)}",
            callback_data=f"stats:{prev_date.isoformat()}"
        ))

    if current_date < max_date:
        next_date = current_date + timedelta(days=1)
        buttons.append(InlineKeyboardButton(
            text=f"{format_day(next_date)} ▶️",
            callback_data=f"stats:{next_date.isoformat()}"
        ))

    return InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
