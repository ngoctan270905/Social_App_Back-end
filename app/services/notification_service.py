import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

from fastapi import Request

from app.core.websocket import manager
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import Notification, NotificationCreate, NotificationResponse
from app.schemas.posts import UserPublic

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo

    async def create_and_send_notification(
        self,
        *,
        recipient_id: str,
        actor: UserPublic,
        type: str,
        message: str,
        entity_ref: Dict[str, Any]
    ):
        """
        Lưu thông báo vào DB và gửi real-time notification qua WebSocket.
        """
        # 1. Tạo và lưu notification vào DB
        print(f"testttt {recipient_id}")
        notification_to_create = NotificationCreate(
            recipient_id=recipient_id,
            actor=actor,
            type=type,
            entity_ref=entity_ref
        )
        await self.notification_repo.create(notification_to_create.model_dump())

        # 2. Chuẩn bị payload cho real-time
        realtime_payload = NotificationResponse(
            type=type,
            message=message,
            data={
                "actor": actor.model_dump(),
                **entity_ref
            }
        )
        
        # 3. Phát sóng qua Redis để WebSocket manager xử lý
        await manager.broadcast_via_redis(
            target_user_ids=[recipient_id],
            payload=realtime_payload.model_dump()
        )

    async def get_notifications_for_user(self, user_id: str, limit: int, cursor: str | None) -> list[Notification]:
        """
        Lấy danh sách thông báo cho một người dùng.
        """
        
        notifications_data = await self.notification_repo.get_by_recipient(
            recipient_id=user_id,
            limit=limit,
            cursor=cursor
        )
        return [Notification.model_validate(n) for n in notifications_data]

    # =================================================================
    # LEGACY SSE METHODS (Not used for new comment notifications)
    # =================================================================
    async def notification_generator(self, request: Request) -> AsyncGenerator[str, None]:
        """
        Hàm sinh dữ liệu SSE chuẩn.
        """
        yield ": ping\n\n"
        
        # This part is for SSE and uses a different NotificationResponse schema
        # For now, we leave it as is.
        welcome_notification_data = {
            "title": "Kết nối thành công",
            "message": "Chào bạn",
            "type": "success"
        }
        yield self._format_sse(welcome_notification_data)

        try:
            while True:
                if await request.is_disconnected():
                    logger.info("Client SSE đã ngắt kết nối.")
                    break
                await asyncio.sleep(15)
                yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            logger.info("Stream SSE bị hủy.")
        except Exception as e:
            logger.error(f"Lỗi Stream SSE: {e}")

    def _format_sse(self, data: dict) -> str:
        json_data = json.dumps(data)
        return f"data: {json_data}\n\n"