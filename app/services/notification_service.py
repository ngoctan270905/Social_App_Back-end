import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any

from fastapi import Request

from app.core.websocket import manager, NOTIFICATION_CHANNEL
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import Notification, NotificationCreate, NotificationResponse
from app.schemas.posts import UserPublic

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.notification_repo = notification_repo


    # Lưu thông báo vào DB và gửi real-time notification qua WebSocket =================================================
    async def create_and_send_notification(self, *,
        recipient_id: str,
        actor: UserPublic,
        type: str,
        message: str,
        entity_ref: Dict[str, Any]
    ):

        notification_to_create = NotificationCreate(
            recipient_id=recipient_id,
            actor=actor,
            type=type,
            message=message,
            entity_ref=entity_ref,
            created_at=datetime.utcnow()
        )
        await self.notification_repo.create(notification_to_create.model_dump())

        # payload cho real-time
        realtime_payload = NotificationResponse(
            type=type,
            message=message,
            data={
                "actor": actor.model_dump(),
                **entity_ref
            }
        )

        # bắn lên redis
        await manager.broadcast_via_redis(
            channel=NOTIFICATION_CHANNEL,
            target_user_ids=[recipient_id],
            payload=realtime_payload.model_dump()
        )

    # Lấy danh sách thông báo ==========================================================================================
    async def get_notifications_for_user(self, user_id: str, limit: int, cursor: str | None) -> list[Notification]:

        notifications_data = await self.notification_repo.get_by_recipient(
            recipient_id=user_id,
            limit=limit,
            cursor=cursor
        )
        notifications: list[Notification] = []

        for notification_doc in notifications_data:
            notification = Notification(
                _id = str(notification_doc["_id"]),
                recipient_id = notification_doc["recipient_id"],
                actor = notification_doc["actor"],
                type = notification_doc["type"],
                message = notification_doc["message"],
                is_read = notification_doc.get("is_read", False),
                entity_ref = notification_doc["entity_ref"],
                created_at = notification_doc["created_at"]
            )
            notifications.append(notification)

        return notifications




    # =================================================================
    # LEGACY SSE METHODS (Not used for new comment notifications)
    # =================================================================
    # async def notification_generator(self, request: Request) -> AsyncGenerator[str, None]:
    #     """
    #     Hàm sinh dữ liệu SSE chuẩn.
    #     """
    #     yield ": ping\n\n"
    #
    #     # This part is for SSE and uses a different NotificationResponse schema
    #     # For now, we leave it as is.
    #     welcome_notification_data = {
    #         "title": "Kết nối thành công",
    #         "message": "Chào bạn",
    #         "type": "success"
    #     }
    #     yield self._format_sse(welcome_notification_data)
    #
    #     try:
    #         while True:
    #             if await request.is_disconnected():
    #                 logger.info("Client SSE đã ngắt kết nối.")
    #                 break
    #             await asyncio.sleep(15)
    #             yield ": heartbeat\n\n"
    #     except asyncio.CancelledError:
    #         logger.info("Stream SSE bị hủy.")
    #     except Exception as e:
    #         logger.error(f"Lỗi Stream SSE: {e}")
    #
    # def _format_sse(self, data: dict) -> str:
    #     json_data = json.dumps(data)
    #     return f"data: {json_data}\n\n"