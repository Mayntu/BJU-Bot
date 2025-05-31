from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from uuid import UUID


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