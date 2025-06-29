import pytz

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timedelta

from db.models import User, Payment
from bot.config import (
    FREE_MEAL_COUNT,
    FREE_TRIAL_DAYS,
    FREE_MEAL_END_MESSAGE,
    SUBSCRIPTION_NOT_ACTIVE_MESSAGE,
    YOOKASSA_PAYMENT_STATUS
)
from bot.services.logger import logger


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
        
        now = datetime.now(pytz.UTC)

        payment = await Payment.filter(
            user=user,
            status=YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value,
            user_subscription__start_date__lte=now.date(),
            user_subscription__end_date__gte=now.date()
        ).first()

        logger.info(f"{payment}")
        if payment:
            logger.info("ok")
            return await handler(event, data)

        had_subscription = await Payment.filter(
            user=user,
            status=YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value
        ).exists()

        logger.info(f"had_subscription : {had_subscription}")

        if not had_subscription and user.created_at and (now - user.created_at) < timedelta(days=FREE_TRIAL_DAYS):
            logger.info("ok2")
            return await handler(event, data)

        msg = SUBSCRIPTION_NOT_ACTIVE_MESSAGE if had_subscription else FREE_MEAL_END_MESSAGE

        if isinstance(event, CallbackQuery):
            logger.info("ok3")
            await event.answer(msg, show_alert=True)
            await event.message.answer(msg)
        elif isinstance(event, Message):
            logger.info("ok3")
            await event.answer(msg)
        
        logger.info("return")
        return
