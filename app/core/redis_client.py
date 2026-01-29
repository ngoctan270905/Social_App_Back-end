import redis.asyncio as redis
from typing import AsyncGenerator
from app.core.config import settings

# Global connection pool duy nhất cho toàn bộ app
redis_pool: redis.ConnectionPool | None = None

# Khởi tạo connection pool =============================================================================================
async def get_redis_pool() -> redis.ConnectionPool:
    global redis_pool
    if redis_pool is None:
        redis_pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    return redis_pool


# Đóng connection pool =================================================================================================
async def close_redis_pool():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None


# Tạo object redis client ==============================================================================================
async def get_redis_client() -> AsyncGenerator[redis.Redis, None]:
    pool = await get_redis_pool()
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


# OB redis client cho background task ==================================================================================
async def get_direct_redis_client() -> redis.Redis:
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)