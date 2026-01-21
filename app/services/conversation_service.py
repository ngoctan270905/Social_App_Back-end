from typing import Optional
from app.repositories.conversation_repository import ConversationRepository
from app.services.participant_service import ParticipantService

class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        participant_service: ParticipantService
    ):
        self.conversation_repo = conversation_repo
        self.participant_service = participant_service

    async def create_private_chat(self, user_id_1: str, user_id_2: str) -> str:
        new_conversation = await self.conversation_repo.create(is_group=False)
        conversation_id = str(new_conversation["_id"])

        participants = await self.participant_service.add_participants(conversation_id, [user_id_1, user_id_2])

        return conversation_id

    async def get_or_create_private_conversation(self, sender_id: str, target_user_id: str) -> str:
        exciting_conversation_id = await self.participant_service.find_direct_conversation_id(sender_id, target_user_id)

        if exciting_conversation_id:
            return exciting_conversation_id

        return await self.create_private_chat(sender_id, target_user_id)