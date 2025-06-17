import pytz

from datetime import datetime, date, timedelta, timezone
from functools import wraps

from db.models import User
from bot.services.logger import logger
from bot.redis.client import redis_client
from bot.exceptions.user import ReportLimitExceeded
from bot.config import REPORT_CONFIG


async def create_user_if_not_exists(user_id: int, username: str) -> User:
    """
    Создает нового пользователя в базе данных.
    
    :param user_id: ID пользователя
    :param username: Имя пользователя
    :return: Объект User
    """
    user = await User.get_or_create(id=user_id, defaults={"username": username})
    logger.info(f"Пользователь {user_id} с именем {username} {'создан' if user[1] else 'уже существует'} в БД.")
    return user[0]


async def get_user(user_id : int) -> User:
    return await User.get_or_none(id=user_id)


async def save_utm_source_if_not_exists(user_id : int, utm_source) -> None:
    user : User = await User.get(id=user_id)
    
    if user.utm_source: return

    user.utm_source = utm_source
    await user.save()


async def set_calories_goal(user_id : int, goal : str) -> None:
    """
    Устанавливает цель по калориям для пользователя.
    
    :param user_id: ID пользователя
    :param goal: Цель по калориям как строка, которая будет преобразована в число с плавующей точкой
    :raises ValueError: Если цель не в диапазоне от 200 до 10000
    :return: None
    """
    try:
        goal : float = float(goal)
        if not 200 <= goal <= 10000:
            raise ValueError("Пожалуйста, введите корректное число от 200 до 10000.")
    except Exception as e:
        raise ValueError("Пожалуйста, введите корректное число от 200 до 10000.")
    
    user : User = await User.get(id=user_id)
    user.calorie_goal = goal
    await user.save()


async def get_user_local_date(user_id : int, shift_days : int = 0) -> date:
    """
    Возвращает текущую локальную дату пользователя, со сдвигом (для листания).

    :param user_id: ID пользователя
    :shift_days: Сдвиг дней
    :return: Дату локального времени пользователя
    """
    user : User = await User.get(id=user_id)
    tz = pytz.timezone(user.timezone)
    now = datetime.now(tz)
    return (now + timedelta(days=shift_days)).date()


async def update_user_timezone(user_id : int, tz_name : str) -> None:
    user : User = await User.filter(id=user_id).first()
    user.timezone = tz_name
    user.timezone_setted = True
    await user.save()


async def check_limit_reports(user_id : int, limit : int = REPORT_CONFIG.LIMIT, hours : int = REPORT_CONFIG.HOURS):
    now = datetime.now(timezone.utc)
    # округляем время до часа, получаем префикс на каждый N-часовой слот
    window_key = now.strftime('%Y-%m-%dT%H')
    redis_key = f"user:{user_id}:limit:{window_key}:h{hours}"

    current = await redis_client.get(redis_key)
    current = int(current) if current else 0

    if current >= limit:
        raise ReportLimitExceeded(hours=hours, max_limit=limit)

    # инкрементируем и устанавливаем TTL
    await redis_client.incr(redis_key)
    await redis_client.expire(redis_key, hours * 3600)



def get_timezone_by_offset(offset_hours: int) -> str:
    now = datetime.now(timezone.utc)
    for tz_name in pytz.all_timezones:
        tz = pytz.timezone(tz_name)
        offset = now.astimezone(tz).utcoffset()
        if offset == timedelta(hours=offset_hours):
            return tz_name
    return "UTC"
