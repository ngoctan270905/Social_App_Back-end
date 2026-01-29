import asyncio
import json
import uuid
import sys
import os
import time
from typing import List

# Thêm đường dẫn project vào sys.path để import được app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.redis_client import get_direct_redis_client

# Cấu hình test
NUM_USERS = 500  # Giảm xuống 500 để test thử độ ổn định trước khi lên 1000
WS_URL = "ws://localhost:8000/api/v1/ws/chat"
CONNECTION_DELAY = 0.05  # Tăng delay lên 50ms để tránh bị Rate Limit chặn sớm

# Biến toàn cục để đo đếm
connected_clients = 0
received_messages = 0
start_broadcast_time = 0

def create_fake_token(user_id: str) -> str:
    """Tạo JWT token giả lập hợp lệ"""
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = {
        "exp": expire,
        "scope": "access_token",
        "sub": user_id,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def simulate_user(user_id: str):
    """Giả lập 1 user kết nối và chờ tin nhắn"""
    global connected_clients, received_messages
    token = create_fake_token(user_id)
    url = f"{WS_URL}?token={token}"
    
    # Thêm Origin để tránh bị CORS chặn (nếu có)
    headers = {
        "Origin": "http://localhost:5173"
    }

    try:
        # async with websockets.connect(url, extra_headers=headers) as websocket: # Gây lỗi ở một số phiên bản
        async with websockets.connect(url) as websocket:
            connected_clients += 1
            if connected_clients % 50 == 0:
                print(f"🔌 Đã kết nối: {connected_clients}/{NUM_USERS} users")

            try:
                while True:
                    await websocket.recv()
                    received_messages += 1
            except websockets.exceptions.ConnectionClosed:
                pass
    except Exception as e:
        # Nếu gặp 403, có khả năng cao là bị Rate Limit của server chặn
        if "403" in str(e):
            # print(f"❌ User {user_id} bị chặn (403). Có thể do Rate Limit.")
            pass
        else:
            print(f"❌ User {user_id} lỗi: {e}")
    finally:
        connected_clients -= 1

async def trigger_broadcast():
    """Gửi tin nhắn broadcast qua Redis để test tốc độ"""
    redis = await get_direct_redis_client()
    
    # Tạo danh sách target users
    target_ids = [f"test_user_{i}" for i in range(NUM_USERS)]
    
    payload = {
        "type": "TEST_MESSAGE",
        "content": "Hello 1000 users!",
        "timestamp": time.time()
    }
    
    message = {
        "target_user_ids": target_ids,
        "payload": payload
    }
    
    print(f"\n🚀 BẮT ĐẦU BROADCAST TIN NHẮN TỚI {NUM_USERS} USERS...")
    global start_broadcast_time, received_messages
    received_messages = 0 # Reset đếm
    start_broadcast_time = time.time()
    
    await redis.publish("chat_broadcast_channel", json.dumps(message))
    await redis.aclose()

async def monitor():
    """Theo dõi tiến độ nhận tin"""
    global received_messages
    while True:
        if start_broadcast_time > 0:
            elapsed = time.time() - start_broadcast_time
            print(f"⏱️  Sau {elapsed:.2f}s: Đã nhận {received_messages}/{NUM_USERS} tin nhắn")
            
            if received_messages >= NUM_USERS:
                print(f"✅ HOÀN THÀNH! Tổng thời gian để fanout 1000 tin: {elapsed:.4f}s")
                break
        await asyncio.sleep(0.5)

async def main():
    # 1. Khởi tạo danh sách tasks cho users
    user_tasks = []
    for i in range(NUM_USERS):
        user_id = f"test_user_{i}"
        user_tasks.append(asyncio.create_task(simulate_user(user_id)))
        # Connect từ từ để không bị chặn bởi OS limit
        await asyncio.sleep(CONNECTION_DELAY)

    print(f"✅ Đã khởi tạo {NUM_USERS} connections. Chờ ổn định 2s...")
    await asyncio.sleep(2)

    # 2. Bắt đầu test gửi tin
    monitor_task = asyncio.create_task(monitor())
    await trigger_broadcast()

    # 3. Chờ monitor xong
    await monitor_task
    
    print("🏁 Test hoàn tất. Đóng kết nối...")
    # Hủy các task user để đóng kết nối
    for task in user_tasks:
        task.cancel()

if __name__ == "__main__":
    try:
        # Tăng giới hạn file open trên Linux (nếu cần)
        # import resource
        # resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
        pass
    except ImportError:
        pass

    asyncio.run(main())
