from typing import List, Optional

from fastapi.encoders import jsonable_encoder

from app.core.websocket import manager
from app.exceptions.post import ForbiddenError
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.posts import PaginationInfo
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessagesResponse


class MessageService:
    def __init__(self,
                 message_repo: MessageRepository,
                 conversation_service: ConversationService,
                 conversation_repo: ConversationRepository
    ):
        self.message_repo = message_repo
        self.conversation_service = conversation_service
        self.conversation_repo = conversation_repo


    # Logic gửi tin nhắn ===============================================================================================
    async def send_message(self, sender_id: str, conversation_id: str, data: MessageCreate) -> MessageResponse:
        msg = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=data.content
        )

        response_msg = MessageResponse(**msg)

        conversation = await self.conversation_repo.get_by_id(conversation_id)

        # 3. Gửi Realtime
        payload = {
            "type": "new_message",
            "conversation_id": conversation_id,
            "data": jsonable_encoder(response_msg)
        }

        if conversation and "participants" in conversation:
            recipient_ids = []

            for participant in conversation["participants"]:
                user_id = participant.get("user_id")
                if user_id:
                    recipient_ids.append(str(user_id))

            await manager.broadcast_via_redis(recipient_ids, payload)

        return response_msg


    # Lấy danh sách tin nhắn ===========================================================================================
    async def get_messages(self, conversation_id: str, cursor: Optional[str] = None, limit: int = 20
                        ) -> PaginatedMessagesResponse:

        messages = await self.message_repo.get_by_conversation(
            conversation_id=conversation_id,
            cursor=cursor,
            limit=limit + 1
        )

        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        next_cursor = str(messages[-1]["_id"]) if messages else None

        responses = []
        for message in messages:
            responses.append(MessageResponse(**message))

        return PaginatedMessagesResponse(
            data=responses,
            pagination=PaginationInfo(
                next_cursor=next_cursor,
                has_more=has_more,
                limit=limit
            )
        )

    async def delete_message(self, conversation_id: str, message_id: str, user_id: str) -> bool:
        # 1. Lấy thông tin tin nhắn
        message = await self.message_repo.get_by_id(message_id)
        if not message:
            return False

        # 2. Kiểm tra xem tin nhắn có thuộc về conversation_id không (để an toàn)
        if str(message.get("conversation_id")) != conversation_id:
            return False

        # 3. Kiểm tra quyền: Chỉ người gửi (sender_id) mới được xóa
        if str(message["sender_id"]) != user_id:
            raise ForbiddenError()

        # 4. Thực hiện xóa
        deleted = await self.message_repo.delete(message_id)

        conversation = await self.conversation_repo.get_by_id(conversation_id)

        if conversation and "participants" in conversation:
            payload = {
                "type": "message_deleted",
                "conversation_id": conversation_id,
                "data": {"id": message_id}
            }

            recipient_ids = []

            for participant in conversation["participants"]:
                user_id = participant.get("user_id")
                if user_id:
                    recipient_ids.append(str(user_id))

            await manager.broadcast_via_redis(recipient_ids, payload)

        return True
