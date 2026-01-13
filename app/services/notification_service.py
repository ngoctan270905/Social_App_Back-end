import asyncio
import json
import logging
from typing import AsyncGenerator
from fastapi import Request
from app.schemas.notification import NotificationResponse

logger = logging.getLogger(__name__)

class NotificationService:
    async def notification_generator(self, request: Request) -> AsyncGenerator[str, None]:
        """
        Hàm sinh dữ liệu SSE chuẩn.
        """
        yield ": ping\n\n"

        # 1. Gửi thông báo chào mừng
        welcome_notification = NotificationResponse(
            title="Kết nối thành công",
            message="Chào bạn",
            type="success"
        )
        yield self._format_sse(welcome_notification)

        try:
            while True:
                # Kiểm tra nếu client đóng tab hoặc ngắt kết nối
                if await request.is_disconnected():
                    logger.info("Client SSE đã ngắt kết nối.")
                    break

                await asyncio.sleep(15)
                yield ": heartbeat\n\n"
                # ------------------------------

        except asyncio.CancelledError:
            logger.info("Stream SSE bị hủy.")
        except Exception as e:
            logger.error(f"Lỗi Stream SSE: {e}")

    def _format_sse(self, data: NotificationResponse) -> str:
        json_data = data.model_dump_json()
        return f"data: {json_data}\n\n"