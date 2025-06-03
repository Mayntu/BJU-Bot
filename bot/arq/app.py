from tortoise import Tortoise
from arq.connections import RedisSettings

from bot.arq.redis_pool import init_redis_pool, close_redis_pool
from bot.arq.tasks import update_daily_report
from bot.config import TORTOISE_ORM, REDIS_HOST, REDIS_PORT


async def startup(ctx):
    ctx['redis'] = await init_redis_pool()
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()

async def shutdown(ctx):
    await close_redis_pool()

class WorkerSettings:
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT, password=None)
    functions = [update_daily_report]
    on_startup = startup
    on_shutdown = shutdown
