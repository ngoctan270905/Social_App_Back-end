import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Danh sách này chứa tất cả các kết nối đang mở
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Chấp nhận kết nối và lưu vào danh sách"""

        await websocket.accept() # upgrade từ http lên ws
        self.active_connections.append(websocket)
        logger.info(f"Client mới đã kết nối. Tổng số kết nối:: {len(self.active_connections)}")



    def disconnect(self, websocket: WebSocket):
        """Xóa kết nối"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client đã ngắt kết nối. Tổng số kết nối:: {len(self.active_connections)}")

    # gửi đến all client đang kết nối tới websocket
    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception:
                # Nếu gửi lỗi, xóa kết nối
                self.disconnect(connection)


    async def handle_message(self, websocket: WebSocket, data: str):
        if data == "ping":
            await websocket.send_text("pong")
        else:
            await websocket.send_text(f"Server received: {data}")

manager = ConnectionManager()
