from tortoise.transactions import in_transaction
from yookassa import Configuration, Payment as YooPayment
from yookassa.domain.response import PaymentResponse as APIPaymentResponse
from yookassa.domain.exceptions import ApiError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import UTC as pytz_UTC
from uuid import uuid4

from bot.config import BOT_TELEGRAM_URL, YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, RECEIPT_EMAIL, SubscriptionsStore, YOOKASSA_PAYMENT_STATUS
from db.models import User, UserSubscription, Payment
from bot.schemas.payments import CreatePaymentTicketResponse
from bot.services.logger import logger


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY


async def create_payment_ticket(user_id : int, subscription_duration : int) -> CreatePaymentTicketResponse:
    """
    Создает платежный тикет и возвращает URL для оплаты.
    
    :param user_id: ID пользователя
    :param subscription_duration: Название подписки
    :raises ValueError: Если подписка с указанным названием не найдена
    :return: Объект ответа API с информацией о платеже
    """
    subscription: SubscriptionsStore = SubscriptionsStore.get_by_duration(duration=subscription_duration)
    if not subscription:
        raise ValueError(f"Подписка с продолжительностью '{subscription_duration}' не найдена.")

    existing_payment = await Payment.filter(
        user_id=user_id,
        status=YOOKASSA_PAYMENT_STATUS.PENDING.value
    ).select_related("user_subscription").order_by('-created_at').first()

    if existing_payment:
        raise ValueError("У вас уже есть активный тикет. Отмените его.")
    
    # Проверка на активную подписку — блокировка подписки, если уже есть
    active_sub : UserSubscription = await UserSubscription.filter(
        user_id=user_id,
        end_date__gte=datetime.now(pytz_UTC).date()
    ).first()

    if active_sub:
        raise ValueError("У вас уже есть активная подписка.")

    # Создание нового платежа и подписки
    logger.info(f"Создание платежного тикета для пользователя {user_id} с подпиской {subscription.title}")
    payment: Payment = await create_payment_db(user_id, subscription)
    ticket: APIPaymentResponse = await get_ticket(payment.id)

    return CreatePaymentTicketResponse(
        confirmation_url=ticket.confirmation.confirmation_url,
        payment_id=str(payment.id)
    )


async def create_payment_db(user_id : int, subscription : SubscriptionsStore) -> Payment:
    """
    Создает запись о платеже в базе данных.
    :param user_id: ID пользователя
    :param subscription: Объект подписки
    :return: Объект Payment
    """
    now_utc = datetime.now(pytz_UTC).date()
    end_utc = now_utc + relativedelta(months=subscription.duration_month)

    async with in_transaction():
        user = await User.get(id=user_id)
        user_subscription = await UserSubscription.create(
            user=user,
            plan=subscription.title,
            price=subscription.price,
            start_date=now_utc,
            end_date=end_utc,
            duration_month=subscription.duration_month
        )
        payment = await Payment.create(
            user=user,
            user_subscription_id=user_subscription.id
        )
        return payment


async def get_ticket(payment_id : str) -> APIPaymentResponse:
    """
    Получает платежный тикет ЮKassa по ID платежа.
    :param payment_id: ID платежа
    :return: Объект ответа API с информацией о платеже
    """
    print(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
    print(Configuration.account_id, Configuration.secret_key)
    payment : Payment = await Payment.get_or_none(id=payment_id).select_related("user_subscription")
    ticket : APIPaymentResponse = YooPayment.create({
        "amount": {
            "value": "{:.2f}".format(payment.user_subscription.price),
            "currency": f"{payment.user_subscription.currency}"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": BOT_TELEGRAM_URL
        },
        "capture": True,
        "description": f"Подписка {payment.user_subscription.plan} {payment.user_subscription.price} {payment.user_subscription.currency}",
        "receipt": {
            "customer": {
                "email": RECEIPT_EMAIL
            },
            "items": [
                {
                    "description": f"Подписка на {payment.user_subscription.plan}",
                    "quantity": "1.00",
                    "amount": {
                        "value": "{:.2f}".format(payment.user_subscription.price),
                        "currency": f"{payment.user_subscription.currency}"
                    },
                    "vat_code": 1,  # Без НДС
                    "payment_mode": "full_prepayment",
                    "payment_subject": "service"
                }
            ]
        }
    }, uuid4())
    logger.info(f"Создан платежный тикет: {ticket.id} для платежа {payment_id}")
    logger.info(payment)
    payment.yookassa_payment_id = ticket.id
    await payment.save()
    return ticket


async def cancel_pending_payment(user_id: int) -> bool:
    """
    Отменяет активный ожидающий платеж пользователя (если есть).
    :param user_id: ID пользователя
    :return: Возвращает True если отмена произошла, иначе False.
    """
    pending_payment = await Payment.filter(user_id=user_id, status=YOOKASSA_PAYMENT_STATUS.PENDING.value).order_by('-created_at').first()
    if not pending_payment:
        return False

    # Попытка отмены в YooKassa
    if pending_payment.yookassa_payment_id:
        try:
            YooPayment.cancel(pending_payment.yookassa_payment_id)
            logger.info(f"Платёж {pending_payment.yookassa_payment_id} отменён в YooKassa")
        except ApiError as e:
            logger.warning(f"Не удалось отменить платёж в YooKassa: {e}")
        except Exception as e:
            logger.error(f"{e}")

    # Локальная отмена
    pending_payment.status = YOOKASSA_PAYMENT_STATUS.CANCELED
    await pending_payment.save()

    # Удаляем связанную подписку
    if pending_payment.user_subscription_id:
        await UserSubscription.filter(id=pending_payment.user_subscription_id).delete()
        logger.info(f"Удалена подписка {pending_payment.user_subscription_id} при отмене платежа {pending_payment.id}")

    logger.info(f"Ожидающий платёж {pending_payment.id} был отменён пользователем {user_id}")
    return True


async def check_payment_status(payment_id : str) -> bool:
    """
    Проверяет статус платежа по его ID.
    
    :param payment_id: ID платежа
    :return: True, если платеж успешен, иначе False
    """
    # Получаем платеж из базы данных
    payment : Payment = await Payment.get_or_none(id=payment_id)
    if not payment:
        raise ValueError(f"Платеж с ID {payment_id} не найден.")
    
    # Проверяем, завершен ли платеж
    logger.info(f"Проверка статуса платежа {payment_id}...")
    if payment.status == "completed":
        logger.info(f"Платеж {payment_id} уже завершен.")
        return True

    # Получаем ответ от ЮKassa API
    yookassa_response : APIPaymentResponse = YooPayment.find_one(payment.yookassa_payment_id)

    # Проверяем статус платежа
    if yookassa_response.status == YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value:
        payment.status = YOOKASSA_PAYMENT_STATUS.SUCCEEDED.value
        await payment.save()
        logger.info(f"Платеж {payment_id} успешно завершен.")
        return True
    
    logger.info(f"Платеж {payment_id} не завершен. Статус: {yookassa_response.status}")
    return False
