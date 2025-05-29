from db.models import User
from bot.services.logger import logger


async def create_user_if_not_exists(user_id: int, username: str) -> User:
    """
    Создает нового пользователя в базе данных.
    
    :param user_id: ID пользователя
    :param username: Имя пользователя
    :return: Объект User
    """
    user = await User.get_or_create(telegram_id=user_id, defaults={"username": username})
    logger.info(f"Пользователь {user_id} с именем {username} {'создан' if user[1] else 'уже существует'} в БД.")
    return user[0]