from tortoise.transactions import in_transaction
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.response import PaymentResponse as APIPaymentResponse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import UTC as pytz_UTC
from uuid import uuid4

from bot.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, SubscriptionsStore
from db.models import User, UserSubscription, Payment
from bot.schemas.payments import CreatePaymentTicketResponse
from bot.services.logger import logger


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


async def create_payment_ticket(user_id : int, subscription_title : str) -> CreatePaymentTicketResponse:
    """
    Создает платежный тикет и возвращает URL для оплаты.
    
    :param user_id: ID пользователя
    :param subscription: Объект подписки
    :return: Объект ответа API с информацией о платеже
    """
    subscription : SubscriptionsStore = SubscriptionsStore.get_by_title(title=subscription_title)
    if not subscription:
        raise ValueError(f"Подписка с названием '{subscription_title}' не найдена.")
    
    payment : Payment = await create_payment_db(user_id, subscription)
    ticket : APIPaymentResponse = await get_ticket(payment.id)
    return CreatePaymentTicketResponse(ticket.confirmation.confirmation_url, payment.id)


async def create_payment_db(user_id : int, subscription : SubscriptionsStore) -> Payment:
    now_utc = datetime.now(pytz_UTC).date()
    end_utc = now_utc + relativedelta(months=subscription.duration_month)
    
    async with in_transaction():
        user_subscription : UserSubscription = await UserSubscription.create(
            user=await User.get(telegram_id=user_id),
            plan=subscription.title,
            price=subscription.price,
            start_date=now_utc,
            end_date=end_utc
        )
        payment : Payment = await Payment.create(
            user=await User.get(telegram_id=user_id),
            user_subscription_id=user_subscription.id
        )
        return payment


async def get_ticket(payment_id : str) -> APIPaymentResponse:
    payment : Payment = await Payment.get_or_none(id=payment_id).select_related("user_subscription")
    ticket : APIPaymentResponse = YooPayment.create({
        "amount": {
            "value": "{:.2f}".format(payment.user_subscription.price),
            "currency": f"{payment.user_subscription.currency}"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/healthReallyMatters_bot"
        },
        "capture": True,
        "description": f"Подписка {payment.user_subscription.plan} {payment.user_subscription.price} {payment.user_subscription.currency}",
    }, uuid4())
    logger.info(payment)
    payment.yookassa_payment_id = ticket.id
    payment.save()
    return ticket


async def check_payment_status(payment_id : str) -> bool:
    """
    Проверяет статус платежа по его ID.
    
    :param payment_id: ID платежа
    :return: True, если платеж успешен, иначе False
    """
    payment : Payment = await Payment.get_or_none(id=payment_id)
    if not payment:
        raise ValueError(f"Платеж с ID {payment_id} не найден.")
    
    if payment.status == "completed":
        logger.info(f"Платеж {payment_id} уже завершен.")
        return True

    yookassa_response : APIPaymentResponse = YooPayment.find_one(payment.yookassa_payment_id)

    if yookassa_response.status == "succeeded":
        payment.status = "pending"
        await payment.save()
        logger.info(f"Платеж {payment_id} успешно завершен.")
        return True
    
    logger.info(f"Платеж {payment_id} не завершен. Статус: {yookassa_response.status}")
    return False
