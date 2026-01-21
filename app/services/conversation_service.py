from typing import Optional, List, Dict, Any
from app.repositories.conversation_repository import ConversationRepository

class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository):
        self.conversation_repo = conversation_repo


    # Tìm kiếm hoặc thêm cuộc trò truyện ===============================================================================
    async def get_or_create_private_conversation(self, sender_id: str, target_user_id: str) -> str:
        existing_conv = await self.conversation_repo.find_direct_conversation_between_users(sender_id, target_user_id)
        if existing_conv:
            return str(existing_conv["_id"])

        # Tạo mới
        new_conv = await self.conversation_repo.create(user_ids=[sender_id, target_user_id], is_group=False)
        return str(new_conv["_id"])


    # Lấy danh sách chat của người dùng ================================================================================
    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        conversations = await self.conversation_repo.get_conversations_for_user(user_id)
        return conversations
