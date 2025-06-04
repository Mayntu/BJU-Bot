import pytz

from datetime import datetime, timedelta
from tortoise.transactions import in_transaction
from tortoise.functions import Sum

from db.models import User, Meal, UserDailyReport, UserDailyMeal
from bot.services.logger import logger


async def update_daily_report(ctx, user_id: str):
    """
    Обновляет дневной отчёт пользователя, суммируя данные о приёмах пищи за текущий день.
    :param ctx: Контекст задачи
    :param user_id: ID пользователя, для которого обновляется отчёт
    """
    logger.info(f"Обновляем дневной отчёт для пользователя: {user_id}...")

    # Получаем пользователя и его таймзону
    user = await User.get(id=user_id)
    user.meal_count += 1
    await user.save()

    user_tz = pytz.timezone(user.timezone)

    # Текущий момент в локальном времени пользователя
    now_user_tz = datetime.now(user_tz)

    # Начало и конец суток пользователя в его локальном времени
    today_start = now_user_tz.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    # Переводим эти границы в UTC
    today_start_utc = today_start.astimezone(pytz.UTC)
    tomorrow_start_utc = tomorrow_start.astimezone(pytz.UTC)

    # Получаем все приёмы пищи за эти сутки
    meals = await Meal.filter(
        user_id=user_id,
        created_at__gte=today_start_utc,
        created_at__lt=tomorrow_start_utc
    ).order_by("created_at")

    # Агрегируем общие показатели за день
    agg = await Meal.filter(
        user_id=user_id,
        created_at__gte=today_start_utc,
        created_at__lt=tomorrow_start_utc
    ).annotate(
        total_weight=Sum("total_weight"),
        total_calories=Sum("total_calories"),
        total_protein=Sum("total_protein"),
        total_fat=Sum("total_fat"),
        total_carbs=Sum("total_carbs"),
        total_fiber=Sum("total_fiber"),
    ).values("total_weight", "total_calories", "total_protein", "total_fat", "total_carbs", "total_fiber")

    totals = agg[0] if agg else {}

    async with in_transaction():
        # Создаём новый дневной отчёт
        await UserDailyReport.filter(user_id=user_id, date=today_start.date()).delete()
        await UserDailyReport.create(
            user_id=user_id,
            date=today_start.date(),
            total_weight=totals.get("total_weight") or 0,
            total_calories=totals.get("total_calories") or 0,
            total_protein=totals.get("total_protein") or 0,
            total_fat=totals.get("total_fat") or 0,
            total_carbs=totals.get("total_carbs") or 0,
            total_fiber=totals.get("total_fiber") or 0,
        )

        # Обновляем список приёмов пищи
        await UserDailyMeal.filter(user_id=user_id, date=today_start.date()).delete()

        for i, meal in enumerate(meals, start=1):
            await UserDailyMeal.create(
                user_id=user_id,
                date=today_start.date(),
                name=meal.name,
                calories=meal.total_calories,
                order=i
            )
    
    logger.info(f"Обновлён дневной отчёт и список приёмов пищи для пользователя: {user_id} — {today_start.date()}")
