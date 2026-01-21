from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ConversationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("conversations")


    # Tạo cuộc trò chuyện ==============================================================================================
    async def create(self, user_ids: List[str], is_group: bool = False) -> Dict[str, Any]:
        now = datetime.utcnow()
        participants = [{"user_id": ObjectId(uid), "joined_at": now} for uid in user_ids]

        doc = {
            "is_group": is_group,
            "participants": participants,
            "created_at": now,
            "updated_at": now
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    # Lấy chi tiết cuộc trò chuyện =====================================================================================
    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(conversation_id)})



    # Tìm cuộc hội thoại giữa 2 người dùng =============================================================================
    async def find_direct_conversation_between_users(self, user_id_1: str, user_id_2: str) -> Optional[Dict[str, Any]]:
        """Tìm cuộc hội thoại 1-1 giữa 2 người dùng."""
        return await self.collection.find_one({
            "is_group": False,
            "participants.user_id": {
                "$all": [ObjectId(user_id_1), ObjectId(user_id_2)]
            },
            # Sicherstellen, dass es genau zwei Teilnehmer gibt
            "participants": {"$size": 2}
        })


    # Lấy danh sách chat của người dùng ================================================================================
    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"participants.user_id": ObjectId(user_id)})
        return await cursor.to_list(length=1000)