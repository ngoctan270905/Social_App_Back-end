from app.repositories.message_repository import MessageRepository
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageResponse

class MessageService:
    def __init__(
        self, 
        message_repo: MessageRepository,
        conversation_service: ConversationService
    ):
        self.message_repo = message_repo
        self.conversation_service = conversation_service

    async def send_message(self, sender_id: str, data: MessageCreate) -> MessageResponse:
        conversation_id = data.conversation_id

        # Nếu chưa có conversation_id, nhờ ConversationService xử lý
        if not conversation_id and data.target_user_id:
            conversation_id = await self.conversation_service.get_or_create_private_conversation(
                sender_id,
                data.target_user_id
            )

        if not conversation_id:
            raise ValueError("Must provide either conversation_id or target_user_id")

        # Lưu tin nhắn
        msg = await self.message_repo.create(
            conversation_id=str(conversation_id),
            sender_id=sender_id,
            content=data.content
        )

        return MessageResponse(**msg)