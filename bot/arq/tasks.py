from datetime import datetime, timedelta
from dateutil.tz import tzutc
from tortoise.transactions import in_transaction
from tortoise.functions import Sum

from db.models import Meal, UserDailyReport
from bot.services.logger import logger


async def update_daily_report(ctx, user_id: str):
    """
    Обновляет дневной отчёт пользователя, суммируя данные о приёмах пищи за текущий день.
    :param ctx: Контекст задачи
    :param user_id: ID пользователя, для которого обновляется отчёт
    """
    logger.info(f"Обновляем общую статистику для: {user_id}...")

    today = datetime.now(tz=tzutc()).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    agg = await Meal.filter(
        user_id=user_id,
        created_at__gte=today,
        created_at__lt=tomorrow
    ).annotate(
        total_weight=Sum("total_weight"),
        total_calories=Sum("total_calories"),
        total_protein=Sum("total_protein"),
        total_fat=Sum("total_fat"),
        total_carbs=Sum("total_carbs"),
        total_fiber=Sum("total_fiber"),
    ).values("total_weight", "total_calories", "total_protein", "total_fat", "total_carbs", "total_fiber")

    totals = agg[0] if agg else {}

    # Проверяем in_transaction, чтобы избежать конфликтов при параллельных обновлениях
    async with in_transaction():
        # Удаляем предыдущий отчёт за сегодня, если он существует и создаём новый с актуальными данными
        await UserDailyReport.filter(user_id=user_id, date=today).delete()
        await UserDailyReport.create(
            user_id=user_id,
            date=today,
            total_weight=totals.get("total_weight") or 0,
            total_calories=totals.get("total_calories") or 0,
            total_protein=totals.get("total_protein") or 0,
            total_fat=totals.get("total_fat") or 0,
            total_carbs=totals.get("total_carbs") or 0,
            total_fiber=totals.get("total_fiber") or 0,
        )

    logger.info(f"Дневной отчёт был обновлён для: {user_id} | дата: {today.date()}.")
