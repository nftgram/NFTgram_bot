import aioredis

from aiogram.contrib.fsm_storage.redis import RedisStorage


class Database:
    pool = None

    async def connect(self, *args, **kwargs):
        self.pool = await aioredis.create_redis_pool(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.pool, name)


database = Database()
storage = RedisStorage()
storage._redis = database
