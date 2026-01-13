import redis.asyncio as redis
from typing import AsyncGenerator
from app.core.config import settings

# Global connection pool
redis_pool: redis.ConnectionPool | None = None

async def get_redis_pool() -> redis.ConnectionPool:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            max_connections=10
        )
    return redis_pool


async def close_redis_pool():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None


async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    pool = await get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()