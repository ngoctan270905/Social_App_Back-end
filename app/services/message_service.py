from typing import List

from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageResponse

class MessageService:
    def __init__(self,
                 message_repo: MessageRepository,
                 conversation_service: ConversationService
    ):
        self.message_repo = message_repo
        self.conversation_service = conversation_service


    # Logic gửi tin nhắn ===============================================================================================
    async def send_message(self, sender_id: str, data: MessageCreate) -> MessageResponse:
        conversation_id = data.conversation_id

        # Nếu chưa có conversation_id tìm phòng chat hoặc tạo mới
        if not conversation_id and data.target_user_id:
            conversation_id = await self.conversation_service.get_or_create_private_conversation(
                sender_id,
                data.target_user_id
            )

        msg = await self.message_repo.create(
            conversation_id=str(conversation_id),
            sender_id=sender_id,
            content=data.content
        )
        return MessageResponse(**msg)

    async def detail_message(self, conversation_id: str, limit: int = 50, skip: int = 0) -> List[MessageResponse]:
        get_message = await self.message_repo.get_by_conversation(conversation_id=conversation_id, limit=limit, skip=skip)
        return get_message