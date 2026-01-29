# Triển Khai Redis Pub/Sub cho Hệ Thống Chat

Tài liệu này hướng dẫn chi tiết các bước thay đổi code để chuyển từ gửi WebSocket trực tiếp sang mô hình Pub/Sub.

## 1. app/core/redis_client.py
Chúng ta cần thêm một client chuyên dụng cho Pub/Sub vì Redis Pub/Sub connection thường phải giữ kết nối liên tục (blocking), không nên dùng chung với Pool thông thường nếu không cần thiết, hoặc đơn giản là thêm helper function.

**Thêm vào cuối file:**

```python
# Helper đơn giản để lấy client trực tiếp không qua generator (dùng cho background tasks)
async def get_direct_redis_client() -> redis.Redis:
    pool = await get_redis_pool()
    return redis.Redis(connection_pool=pool)
```

---

## 2. app/core/websocket.py
Đây là nơi thay đổi lớn nhất. Manager cần khả năng "lắng nghe" Redis.

**Code Cũ:**
```python
    # gửi đến user
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {user_id}: {e}")
```

**Code Mới (Kế hoạch):**
Ta sẽ thêm logic `subscribe` và xử lý tin nhắn từ Redis.

```python
import json
import asyncio
from typing import List, Dict
from fastapi import WebSocket
from loguru import logger
from app.core.redis_client import get_direct_redis_client

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.pubsub_client = None

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected.")

    def disconnect(self, websocket: WebSocket, user_id: str):
        # ... (giữ nguyên logic disconnect cũ)
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    # --- PHẦN MỚI: REDIS PUB/SUB ---

    async def start_listening_redis(self):
        """Hàm này sẽ được gọi khi Server khởi động (trong lifespan)"""
        redis = await get_direct_redis_client()
        self.pubsub_client = redis.pubsub()
        await self.pubsub_client.subscribe("chat_broadcast_channel")
        
        async for message in self.pubsub_client.listen():
            if message["type"] == "message":
                await self.process_redis_message(message["data"])

    async def process_redis_message(self, raw_data: str):
        """
        Nhận tin từ Redis -> Tìm xem User có đang kết nối ở Server này không -> Gửi
        Format tin nhắn mong đợi từ Redis:
        {
            "target_user_ids": ["user_1", "user_2"], 
            "payload": { ... nội dung tin nhắn ... }
        }
        """
        try:
            data = json.loads(raw_data)
            target_ids = data.get("target_user_ids", [])
            payload = data.get("payload", {})

            # Logic Fan-out tại Server Local
            # Chỉ gửi cho những user đang kết nối tới Server Instance này
            for user_id in target_ids:
                if user_id in self.active_connections:
                    for connection in self.active_connections[user_id]:
                        try:
                            await connection.send_json(payload)
                        except Exception as e:
                            logger.error(f"Error sending socket to {user_id}: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing redis message: {e}")

    async def broadcast_via_redis(self, target_user_ids: List[str], payload: dict):
        """Thay vì gửi trực tiếp, ta bắn lên Redis"""
        redis = await get_direct_redis_client()
        message = {
            "target_user_ids": target_user_ids,
            "payload": payload
        }
        await redis.publish("chat_broadcast_channel", json.dumps(message))

manager = ConnectionManager()
```

---

## 3. app/core/lifespan.py
Cần khởi chạy listener khi ứng dụng bắt đầu.

**Thêm vào startup:**
```python
# Giả định lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... code cũ ...
    
    # Chạy background task lắng nghe Redis
    asyncio.create_task(manager.start_listening_redis())
    
    yield
    # ... shutdown logic ...
```

---

## 4. app/services/message_service.py
Thay đổi cách gọi manager.

**Code Cũ:**
```python
        if conversation and "participants" in conversation:
            for p in conversation["participants"]:
                p_id = str(p["user_id"])
                await manager.send_personal_message(payload, p_id)
```

**Code Mới:**
Thay vòng lặp gửi từng người bằng **1 lệnh gửi duy nhất** lên Redis (kèm danh sách người nhận).

```python
        if conversation and "participants" in conversation:
            # Thu thập tất cả ID người nhận
            recipient_ids = [str(p["user_id"]) for p in conversation["participants"]]
            
            # Gửi 1 lần duy nhất lên Redis
            # Manager sẽ tự lo việc phân phối
            await manager.broadcast_via_redis(recipient_ids, payload)
```

## Tóm tắt Lợi Ích
1.  **MessageService** chạy cực nhanh: Nó chỉ gom ID và bắn 1 cục JSON lên Redis rồi xong việc. Không phải chờ I/O socket.
2.  **Scalability**: Nếu bạn chạy 2 server, Server A bắn tin lên Redis, Server B cũng nhận được tin đó từ Redis -> Server B thấy User đích đang kết nối với mình -> Server B gửi tin xuống. User nhận được tin dù đang ở server nào.
