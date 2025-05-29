import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from bot.config import BOT_TOKEN
from bot.handlers import base, food_analyze
from db.init import init_db

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

dp.include_router(base.router)
dp.include_router(food_analyze.router)

async def on_startup():
    await init_db()

async def main():
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    # )
    asyncio.run(main())
