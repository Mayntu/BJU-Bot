from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.config import BUY_TEXT, HELLO_TEXT, HELP_TEXT, SUBSCRIBE_TEXT, OFERTA_FILE_ID
from bot.services.user import create_user_if_not_exists, get_timezone_by_offset, update_user_timezone, save_utm_source_if_not_exists
from bot.services.payments import create_payment_ticket, check_payment_status, cancel_pending_payment
from bot.services.utm import parse_utm_source
from bot.services.logger import logger
from bot.keyboards.menu import (
    get_subscriptions_menu,
    get_subscription_confirmation_menu,
    get_keyboard_remove,
    get_timezone_offset_keyboard
)
from bot.states.user import TimezoneState
from bot.handlers.food_analyze import show_stats

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


@router.callback_query(F.data.startswith("choose_offset:"), TimezoneState.waiting_for_offset)
async def handle_timezone_choice(callback: CallbackQuery, state: FSMContext):
    offset = int(callback.data.split(":")[1])
    tz_name = get_timezone_by_offset(offset)

    await update_user_timezone(user_id=callback.from_user.id, tz_name=tz_name)

    await callback.message.edit_text(
        f"✅ Ваш часовой пояс установлен: (UTC{offset:+d})",
        parse_mode="Markdown"
    )

    data = await state.get_data()
    await state.clear()
    
    if data.get("show_stats_after_tz"):
        await show_stats(user_id=callback.from_user.id, chat_id=callback.message.chat.id, bot=callback.bot)



# ------------------- Commands ------------------- #

# Обработка команды /start
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id : int = message.from_user.id

    await create_user_if_not_exists(
        user_id=user_id,
        username=message.from_user.username or "Unknown"
    )

    payload = message.text.split(" ", 1)
    start_param = payload[1] if len(payload) > 1 else ""

    # utm_source : str = parse_utm_source(start_param=start_param)
    utm_source : str = start_param

    await save_utm_source_if_not_exists(
        user_id=user_id,
        utm_source=utm_source
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


@router.message(Command("set_timezone"))
async def ask_timezone(message: Message, state: FSMContext):
    await state.set_state(TimezoneState.waiting_for_offset)
    await state.update_data(show_stats_after_tz=False)
    await message.answer(
        "Выберите ваш часовой пояс:",
        reply_markup=get_timezone_offset_keyboard()
    )
