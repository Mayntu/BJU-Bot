from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from bot.config import BUY_TEXT, HELLO_TEXT, HELP_TEXT, SUBSCRIBE_TEXT, OFERTA_FILE_ID
from bot.schemas.payments import CreatePaymentTicketResponse
from bot.services.user import create_user_if_not_exists
from bot.services.payments import create_payment_ticket, check_payment_status, cancel_pending_payment
from bot.services.logger import logger
from bot.keyboards.menu import (
    get_subscriptions_menu,
    get_subscription_confirmation_menu,
    get_keyboard_remove,
)

router : Router = Router()


# ------------------- Callbacks ------------------- #

# Обработка нажатия на кнопку подписки
@router.callback_query(F.data.startswith("sub_duration:"))
async def handle_subscription(callback_query : CallbackQuery):
    # await callback_query.message.delete()
    duration : int = int(callback_query.data.split(":")[1])
    
    await callback_query.answer(f"Вы выбрали подписку на {duration} мес.")

    # Создаем платежный тикет для подписки
    try:
        create_ticket_response = await create_payment_ticket(
            user_id=callback_query.from_user.id,
            subscription_duration=duration
        )
    except ValueError as e:
        await callback_query.answer(str(e), show_alert=True)
        await callback_query.message.answer(
            text="⚠️ " + str(e)
        )
        return

    await callback_query.message.answer(
        text=BUY_TEXT.format(duration=duration),
        reply_markup=get_subscription_confirmation_menu(
            url=create_ticket_response.confirmation_url,
            payment_id=create_ticket_response.payment_id
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
            "✅ Платеж успешно подтвержден! Спасибо за подписку!"
        )
        await callback_query.message.delete()
        return
    
    # Если платеж не подтвержден, отправляем сообщение об ошибке
    await callback_query.message.answer(
        "❌ Платеж не совершён или не подтвержден. Попробуйте еще раз."
    )


@router.callback_query(F.data == "cancel_payment")
async def cancel_user_payment(callback_query: CallbackQuery):
    success = await cancel_pending_payment(user_id=callback_query.from_user.id)

    if success:
        await callback_query.answer("Платёж отменён")
        await callback_query.message.answer("Вы можете снова выбрать подписку:", reply_markup=get_subscriptions_menu())
        await callback_query.message.delete()
    else:
        await callback_query.answer("Нет активного платежа для отмены", show_alert=True)



@router.callback_query(F.data == "show_offer")
async def handle_show_offer(callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer_document(OFERTA_FILE_ID, caption="📄 Ознакомьтесь с офертой")


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
        reply_markup=get_keyboard_remove()
    )


# Обработка команды /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        text=HELP_TEXT
    )


# Обработка команды /subscribe
@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    await message.answer(
        SUBSCRIBE_TEXT,
        reply_markup=get_subscriptions_menu()
    )