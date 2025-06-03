import pytz

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from datetime import datetime

from db.models import Payment
from bot.keyboards.menu import get_subscriptions_menu


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
        
        # Получаем Payment пользователя с успешной подпиской и активным периодом
        now_utc = datetime.now(pytz.UTC).date()
        payment = await Payment.filter(
            user__id=user_id,
            status="succeeded",
            user_subscription__start_date__lte=now_utc,
            user_subscription__end_date__gte=now_utc
        ).first()
        
        if not payment:
            # Нет действующей подписки — отправляем сообщение и прерываем
            if isinstance(event, CallbackQuery):
                await event.answer("❌ Подписка не активна. Пожалуйста, оплатите подписку. /subscribe", show_alert=True)
                await event.message.answer("Ваша подписка не активна. Перейдите в меню подписок.")
            elif isinstance(event, Message):
                await event.answer("❌ Подписка не активна. Пожалуйста, оплатите подписку. /subscribe")
            return
        
        # Всё ок, подписка активна — вызываем хендлер дальше
        return await handler(event, data)
