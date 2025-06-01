import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import BOT_TOKEN
from bot.handlers import base, food_analyze
from bot.arq.redis_pool import init_redis_pool
from db.init import init_db
import db.signals # noqa: F401 # импорт сигналов для регистрации обработчиков


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(base.router)
dp.include_router(food_analyze.router)

async def on_startup():
    await init_redis_pool()
    await init_db()

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
