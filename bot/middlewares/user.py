# bot/middlewares/user.py
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any
from bot.redis.client import redis_client
from bot.services.user import create_user_if_not_exists

class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id
        key = f"registered_user:{user_id}"

        if not await redis_client.exists(key):
            await create_user_if_not_exists(
                user_id=user_id,
                username=event.from_user.username or "Unknown"
            )
            await redis_client.set(key, "1", ex=60 * 60 * 24 * 7) # неделя

        return await handler(event, data)
