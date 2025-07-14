from arq import cron
from arq.connections import RedisSettings
from tortoise import Tortoise
from datetime import date

from bot.arq.redis_pool import init_redis_pool, close_redis_pool
from bot.arq.tasks import (
    update_daily_report,
    notify_users_day_2,
    notify_users_day_3,
    notify_users_trial_ending, # DAY 4
    notify_users_day_7,
    notify_old_users_about_system_change
)
from bot.config import TORTOISE_ORM, REDIS_HOST, REDIS_PORT
from run import bot


async def startup(ctx):
    ctx['redis'] = await init_redis_pool()
    ctx['bot'] = bot
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

async def shutdown(ctx):
    await close_redis_pool()


class WorkerSettings:
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT, password=None)
    functions = [update_daily_report, notify_users_trial_ending, notify_old_users_about_system_change]
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(notify_users_day_2, hour=9, minute=0),      # 12:00 МСК
        cron(notify_users_day_3, hour=8, minute=30),     # 11:30 МСК
        cron(notify_users_trial_ending, hour=7, minute=30),  # 10:30 МСК DAY 4
        cron(notify_users_day_7, hour=16, minute=30),    # 19:30 МСК
        cron(
            notify_old_users_about_system_change,
            hour=10,
            minute=0
        ),
    ]
