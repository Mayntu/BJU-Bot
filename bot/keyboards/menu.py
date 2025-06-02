from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import SubscriptionsStore as Store

def get_main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="/stats")],
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/subscribe")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Отправь фото еды, текст или аудио..."
    )

def get_subscriptions_menu() -> InlineKeyboardMarkup:
    inline_keyboard : list[list[InlineKeyboardButton]] = []
    for subscription in Store:
        price : float = subscription.price
        title : str = subscription.title
        duration = subscription.duration_month
        button_text = f"Тарифный план [{subscription.title}] – {price} руб."
        inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"sub_title:{title}"
            )
        ])


    return InlineKeyboardMarkup(
        inline_keyboard=inline_keyboard
    )

def get_subscription_confirmation_menu(url : str, payment_id : str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Оплатить", url=url),
            InlineKeyboardButton(text="🔍 Проверить", callback_data=f"subscription_payment_id:{payment_id}")
        ]
    ])

    return keyboard
