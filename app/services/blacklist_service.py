import json
from datetime import timedelta
from typing import Optional
import redis.asyncio as redis

class BlacklistService:
    # hàm khởi tạo
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client


    async def add_to_blacklist(self, jti: str, ttl: int, user_id: Optional[int] = None, exp: Optional[int] = None):
        key = f"jti:{jti}"
        value = json.dumps({
            "jti": jti,
            "user_id": user_id,
            "exp": exp,
            "status": "blacklist"
        })
        await self.redis_client.setex(name=key, time=ttl, value=value)

    # hàm kiểm tra xem jti có trong blacklist ko
    async def is_blacklisted(self, jti: str) -> bool:
        # tạo key
        key = f"jti:{jti}"
        # gọi tới redis EXITS
        return await self.redis_client.exists(key)



