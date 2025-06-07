from aiogram import Bot
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
)

from bot.config import SubscriptionsStore as Store


def get_main_menu() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="/stats")],
        [KeyboardButton(text="/help")],
        [KeyboardButton(text="/subscribe")],
        [KeyboardButton(text="/set_goal")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Отправь фото еды, текст или аудио..."
    )


def get_subscriptions_menu() -> InlineKeyboardMarkup:
    inline_keyboard : list[list[InlineKeyboardButton]] = []

    inline_keyboard.append([
        InlineKeyboardButton(
            text="📄 Ознакомиться с офертой",
            callback_data="show_offer"
        )
    ])

    for subscription in Store:
        price : float = subscription.price
        title : str = subscription.title
        duration : int = subscription.duration_month
        button_text : str = f"{duration} мес: – {price} руб."
        inline_keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"sub_duration:{duration}"
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



async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать"),
        BotCommand(command="subscribe", description="Тарифы"),
        BotCommand(command="help", description="Помощь"),

        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="set_goal", description="Цель по калориям"),
    ]
    await bot.set_my_commands(commands)
