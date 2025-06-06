from db.models import User
from bot.services.logger import logger


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
