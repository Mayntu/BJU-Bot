from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.config import BUY_TEXT, HELLO_TEXT, HELP_TEXT
from bot.schemas.payments import CreatePaymentTicketResponse
from bot.services.user import create_user_if_not_exists
from bot.services.payments import create_payment_ticket, check_payment_status
from bot.keyboards.menu import (
    get_main_menu,
    get_subscriptions_menu,
    get_subscription_confirmation_menu
)

router : Router = Router()

# ------------------- Callbacks ------------------- #

# Обработка нажатия на кнопку подписки
@router.callback_query(F.data.startswith("sub_title:"))
async def handle_subscription(callback_query : CallbackQuery):
    # await callback_query.message.delete()
    title : str = callback_query.data.split(":")[1]
    
    await callback_query.answer(f"Вы выбрали подписку {title}")

    # Создаем платежный тикет для подписки
    create_ticket_response : CreatePaymentTicketResponse = await create_payment_ticket(
        user_id=callback_query.from_user.id,
        subscription_title=title
    )
    
    await callback_query.message.answer(
        text=BUY_TEXT.format(
            title=title
        ),
        reply_markup=get_subscription_confirmation_menu(
            url=create_ticket_response.confirmation_url,
            payment_id=create_ticket_response.payment_id,
        )
    )


@router.callback_query(F.data.startswith("subscription_payment_id:"))
async def handle_subscription_payment(callback_query : CallbackQuery):
    payment_id : str = callback_query.data.split(":")[1]
    
    await callback_query.answer(f"Проверка платежа {payment_id}...")
    
    # Проверяем статус платежа
    # Если платеж подтвержден, отправляем сообщение об успешной подписке
    if await check_payment_status(payment_id=payment_id):
        await callback_query.message.answer(
            "✅ Платеж успешно подтвержден! Спасибо за подписку!",
            reply_markup=get_main_menu()
        )
        return
    
    # Если платеж не подтвержден, отправляем сообщение об ошибке
    await callback_query.message.answer(
        "❌ Платеж не совершён или не подтвержден. Попробуйте еще раз.",
        reply_markup=get_subscriptions_menu()
    )


# ------------------- Commands ------------------- #

# Обработка команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await create_user_if_not_exists(
        user_id=message.from_user.id,
        username=message.from_user.username or "Unknown"
    )
    await message.answer(
        text=HELLO_TEXT,
        reply_markup=get_main_menu()
    )


# Обработка команды /stats
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        text=HELP_TEXT,
        reply_markup=get_main_menu()
    )


# Обработка команды /subscribe
@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    await message.answer(
        "💳 Выберите срок подписки:",
        reply_markup=get_subscriptions_menu()
    )