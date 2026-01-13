from typing import AsyncGenerator

from sqlalchemy import text
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from app.core.config import settings


# Engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    # echo=settings.ENVIRONMENT == "development",
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Async session maker
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

# Hàm test kết nối với db
async def test_db_connection():
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))  # Test simple query
        return True
    except Exception as e:
        raise RuntimeError(f"Lỗi khi kết nối cơ sở dữ liệu: {e}")


# Đóng kết nối connection pool
async def dispose_db():
    await engine.dispose()
