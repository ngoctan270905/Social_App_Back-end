import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
# from app.core.database import test_db_connection
# from app.core.database import dispose_db
from app.core.redis_client import get_redis_pool, close_redis_pool
from .mongo_database import mongodb_client
from loguru import logger

from .websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ================= Startup =================
    logger.info("=" * 50)
    logger.info("Bắt đầu khởi động ứng dụng...")
    logger.info("=" * 50)

    try:
        # 1. Database
        logger.info("Đang kết nối tới cơ sở dữ liệu...")
        # await test_db_connection()
        await mongodb_client.connect()
        logger.info("Kết nối thành công!")

        # 2. Redis pool
        logger.info("Đang kết nối tới Redis...")
        pool = await get_redis_pool()

        # Test connection
        import redis.asyncio as redis
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        await client.aclose()
        logger.info("Kết nối thành công")

        asyncio.create_task(manager.start_listening_redis())
        logger.info("Start Redis Pub/Sub listener")

        logger.info("=" * 50)
        logger.info("Khởi động ứng dụng hoàn tất")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Khởi động ứng dụng thất bại: {e}", exc_info=True)
        raise

    yield

    # ================= Shutdown =================
    logger.info("=" * 50)
    logger.info("Bắt đầu tắt ứng dụng...")
    logger.info("=" * 50)

    try:
        # 1. Redis Listener
        logger.info("Đang dừng Redis Listener...")
        await manager.stop_listening_redis()
        logger.info("Redis Listener đã dừng")

        # 2. Redis Pool
        logger.info("Đang đóng Redis pool...")
        await close_redis_pool()
        logger.info("Redis pool đã được đóng")

        # 2. Database
        logger.info("Đang giải phóng cơ sở dữ liệu...")
        # await dispose_db()
        await mongodb_client.close()
        logger.info("Cơ sở dữ liệu đã được giải phóng")

        logger.info("=" * 50)
        logger.info("Tắt ứng dụng hoàn tất")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Lỗi khi tắt ứng dụng: {e}", exc_info=True)
