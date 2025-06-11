from aiogram import Bot
from aiogram.types import (
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
)

from bot.config import SubscriptionsStore as Store


def get_keyboard_remove() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


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
            InlineKeyboardButton(text="🔍 Проверить", callback_data=f"subscription_payment_id:{payment_id}"),
            InlineKeyboardButton(
                text="❌ Отменить платёж",
                callback_data="cancel_payment"
            )
        ]
    ])

    return keyboard


def get_cancel_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить платёж", callback_data="cancel_payment")]
    ])


def get_timezone_offset_keyboard() -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for i, offset in enumerate(range(-12, 15)):  # от UTC-12 до UTC+14
        label = f"UTC{offset:+d}"
        callback_data = f"choose_offset:{offset}"
        row.append(InlineKeyboardButton(text=label, callback_data=callback_data))

        if len(row) == 4 or offset == 14:  # каждые 4 кнопки
            buttons.append(row)
            row = []

    return InlineKeyboardMarkup(inline_keyboard=buttons)



async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="set_goal", description="Цель по калориям"),
        BotCommand(command="subscribe", description="Тарифы"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="set_timezone", description="Установить часовой пояс")
    ]
    await bot.set_my_commands(commands)
