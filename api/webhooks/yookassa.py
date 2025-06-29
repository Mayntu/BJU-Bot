from fastapi import APIRouter, Request
from yookassa.domain.notification import WebhookNotificationEventType
from yookassa.domain.notification import WebhookNotificationFactory
from yookassa.domain.response import PaymentResponse

from bot.services.logger import logger
from db.models import Payment, User
from bot.config import YOOKASSA_PAYMENT_STATUS
from run import bot

router = APIRouter()


@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request):
    logger.info("Пришёл вебхук")

    try:
        json_data = await request.json()
        notification = WebhookNotificationFactory().create(json_data)
        logger.info("Проверяем notification event")

        if notification.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            logger.info("Оплата прошла успешна")
            payment_object: PaymentResponse = notification.object
            yookassa_payment_id = payment_object.id

            payment = await Payment.get_or_none(yookassa_payment_id=yookassa_payment_id).prefetch_related("user_subscription")

            logger.info("Получаем payment из бд и сохраняем статус успешно")
            if not payment:
                logger.warning(f"Webhook: Платеж не найден: {yookassa_payment_id}")
                return {"status": "not found"}

            payment.status = YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value
            await payment.save()

            logger.info("Платёж успешно сохранён")

            await bot.send_message(
                chat_id=payment.user_id,
                text="✅ Платёж успешно подтверждён! Подписка активирована."
            )

            logger.info("Отправили пользователю сообщение")

            return {"status": "ok"}

    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
        return {"status": "error"}
