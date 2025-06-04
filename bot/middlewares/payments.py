import pytz

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from datetime import datetime

from db.models import User, Payment
from bot.config import (
    FREE_MEAL_COUNT,
    FREE_MEAL_END_MESSAGE,
    SUBSCRIPTION_NOT_ACTIVE_MESSAGE,
    YOOKASSA_PAYMENT_STATUS
)


class SubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки активности подписки пользователя.
    Если подписка не активна, отправляет сообщение и прерывает выполнение хендлера.
    """
    async def __call__(self, handler, event, data):
        user_id = None
        
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif isinstance(event, Message):
            user_id = event.from_user.id
        
        if user_id is None:
            # Если нет user_id
            return await handler(event, data)
        
        user : User = await User.get_or_none(id=user_id)
        if not user:
            # Если пользователь не найден
            if isinstance(event, CallbackQuery):
                await event.answer("❌ Пользователь не найден. Пожалуйста, зарегистрируйтесь.", show_alert=True)
                await event.message.answer("Пожалуйста, зарегистрируйтесь.")
            elif isinstance(event, Message):
                await event.answer("❌ Пользователь не найден. Пожалуйста, зарегистрируйтесь.")
            return
        
        if user.meal_count > FREE_MEAL_COUNT:
            now_utc = datetime.now(pytz.UTC).date()
            payment = await Payment.filter(
                user=user,
                status=YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value,
                user_subscription__start_date__lte=now_utc,
                user_subscription__end_date__gte=now_utc
            ).first()

            if payment:
                return await handler(event, data)
            else:
                # Проверяем, была ли вообще когда-то подписка
                had_subscription = await Payment.filter(
                    user=user,
                    status=YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value
                ).exists()
                if had_subscription:
                    # Подписка была, но закончилась
                    msg = SUBSCRIPTION_NOT_ACTIVE_MESSAGE
                else:
                    # Никогда не было подписки
                    msg = FREE_MEAL_END_MESSAGE

                if isinstance(event, CallbackQuery):
                    await event.answer(msg, show_alert=True)
                    await event.message.answer(msg)
                elif isinstance(event, Message):
                    await event.answer(msg)
                return

        else:
            return await handler(event, data)
