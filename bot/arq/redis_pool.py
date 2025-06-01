from arq.connections import RedisSettings, create_pool

redis_pool = None

async def init_redis_pool():
    global redis_pool
    if redis_pool is None:
        redis_pool = await create_pool(RedisSettings(host="redis", port=6379, password=None))
    return redis_pool

async def close_redis_pool():
    global redis_pool
    if redis_pool:
        redis_pool.close()
        await redis_pool.wait_closed()
        redis_pool = None
