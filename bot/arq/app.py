from arq import cron
from arq.connections import RedisSettings
from tortoise import Tortoise

from bot.arq.redis_pool import init_redis_pool, close_redis_pool
from bot.arq.tasks import update_daily_report, notify_users_trial_ending
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
    functions = [update_daily_report, notify_users_trial_ending]
    on_startup = startup
    on_shutdown = shutdown
    cron_jobs = [
        cron(notify_users_trial_ending, hour=10, minute=0),  # каждый день в 10:00 UTC
    ]
