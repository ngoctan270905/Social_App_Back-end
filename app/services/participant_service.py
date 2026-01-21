from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.repositories.participant_repository import ParticipantRepository

class ParticipantService:
    def __init__(self, participant_repo: ParticipantRepository):
        self.participant_repo = participant_repo

    async def add_participants(self, conversation_id: str, user_ids: List[str]):
        """Thêm danh sách user vào cuộc hội thoại"""
        now = datetime.utcnow()
        participants_data = [
            {
                "conversation_id": ObjectId(conversation_id),
                "user_id": ObjectId(uid),
                "joined_at": now
            }
            for uid in user_ids
        ]
        await self.participant_repo.create_many(participants_data)

    async def find_direct_conversation_id(self, user_id_1: str, user_id_2: str) -> Optional[str]:
        """Tìm ID cuộc hội thoại 1-1 giữa 2 người"""

        # 1. Lấy tất cả hội thoại User 1 tham gia
        user_1_participations = await self.participant_repo.get_by_user(user_id_1)
        user1_conversation_ids = []
        for p in user_1_participations:
            user1_conversation_ids.append(p["conversation_id"])

        if not user1_conversation_ids:
            return None

        # 2. Tìm xem User 2 có trong danh sách hội thoại đó không
        existing_participant = await self.participant_repo.find_one({
            "user_id": ObjectId(user_id_2),
            "conversation_id": {"$in": user1_conversation_ids}
        })

        if existing_participant:
            return str(existing_participant["conversation_id"])
        return None