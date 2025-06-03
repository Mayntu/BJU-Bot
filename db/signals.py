from tortoise.signals import post_save, post_delete

from db.models import Meal
from bot.arq.redis_pool import init_redis_pool

@post_save(Meal)
async def meal_post_save(sender, instance, created, using_db, update_fields):
    redis_pool = await init_redis_pool()
    await redis_pool.enqueue_job('update_daily_report', str(instance.user_id))


@post_delete(Meal)
async def meal_post_delete(sender, instance, using_db):
    redis = await init_redis_pool()
    await redis.enqueue_job('update_daily_report', str(instance.user_id))