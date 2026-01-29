import asyncio
import json
from typing import List, Dict
from fastapi import WebSocket
from loguru import logger
from redis.exceptions import ConnectionError
from app.core.redis_client import get_direct_redis_client

class ConnectionManager:
    def __init__(self):
        # key là user_id: value = list danh sách kết nối
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.pubsub_client = None
        self.is_shutting_down = False


    # Hàm kết nối ======================================================================================================
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept() # upgrade từ http lên ws
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(
            f"User {user_id} đã kết nối. "
            f"Tổng số kết nối: {sum(len(v) for v in self.active_connections.values())}"
        )


    # Hàm ngắt kết nối =================================================================================================
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} Đã ngắt kết nối. Tổng số kết nối: {sum(len(v) for v in self.active_connections.values())}")


    # khởi động ========================================================================================================
    async def start_listening_redis(self):
        try:
            redis = await get_direct_redis_client()
            self.pubsub_client = redis.pubsub()
            await self.pubsub_client.subscribe("chat_broadcast_channel")

            async for message in self.pubsub_client.listen():
                if message["type"] == "message":
                    asyncio.create_task(self.process_redis_message(message["data"]))
        except ConnectionError:
            if self.is_shutting_down:
                logger.info("Redis listener dừng")
            else:
                logger.error("Mất kết nối")
        except Exception as e:
            logger.error(f"Redis dừng hoạt động: {e}")
        finally:
            if self.pubsub_client:
                await self.pubsub_client.close()


    # stop
    async def stop_listening_redis(self):
        self.is_shutting_down = True
        if self.pubsub_client:
            logger.info("Đang hủy đăng ký Redis Pub/Sub...")
            await self.pubsub_client.unsubscribe("chat_broadcast_channel")
            await self.pubsub_client.close()
            logger.info("Đã hủy đăng ký Redis Pub/Sub")


    # Gửi tin nhắn =====================================================================================================
    async def process_redis_message(self, raw_data: str):
        try:
            data = json.loads(raw_data)
            target_ids = data.get("target_user_ids", [])
            payload = data.get("payload", {})

            # for user_id in target_ids:
            #     if user_id in self.active_connections:
            #         for connection in self.active_connections[user_id]:
            #             await connection.send_json(payload)

            tasks = []
            for user_id in target_ids:
                if user_id in self.active_connections:
                    for connection in self.active_connections[user_id]:
                        tasks.append(connection.send_json(payload))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Lỗi khi gửi socket: {res}")

        except Exception as e:
            logger.error(f"Error processing redis message: {e}")


    # bắn event lên redis
    async def broadcast_via_redis(self, target_user_ids: List[str], payload: dict):
        redis = await get_direct_redis_client()
        message = {
            "target_user_ids": target_user_ids,
            "payload": payload
        }
        await redis.publish("chat_broadcast_channel", json.dumps(message))

manager = ConnectionManager()
