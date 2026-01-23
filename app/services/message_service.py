from typing import List, Optional

from app.repositories.message_repository import MessageRepository
from app.schemas.posts import PaginationInfo
from app.services.conversation_service import ConversationService
from app.schemas.message import MessageCreate, MessageResponse, PaginatedMessagesResponse


class MessageService:
    def __init__(self,
                 message_repo: MessageRepository,
                 conversation_service: ConversationService
    ):
        self.message_repo = message_repo
        self.conversation_service = conversation_service


    # Logic gửi tin nhắn ===============================================================================================
    async def send_message(self, sender_id: str, conversation_id: str, data: MessageCreate) -> MessageResponse:
        msg = await self.message_repo.create(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=data.content
        )
        return MessageResponse(**msg)

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
