from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ConversationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("conversations")

    # Tạo cuộc trò chuyện mới ==========================================================================================
    async def create(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(conversation_data)
        conversation_data["_id"] = result.inserted_id
        return conversation_data


    # Lấy chi tiết cuộc trò chuyện =====================================================================================
    async def get_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(conversation_id)})


    # Tìm cuộc trò chuyện 1 - 1 ========================================================================================
    async def find_by_participants(self, participant_ids: List[str]) -> Optional[Dict[str, Any]]:
        object_ids = [ObjectId(p_id) for p_id in participant_ids]

        query = {
            "participants.user_id": {
                "$all": object_ids
            },
            "is_group": False
        }
        result =  await self.collection.find_one(query)
        return result


    # Tìm cuộc hội thoại giữa 2 người dùng =============================================================================
    async def find_direct_conversation_between_users(self, user_id_1: str, user_id_2: str) -> Optional[Dict[str, Any]]:

        return await self.collection.find_one({
            "is_group": False,
            "participants.user_id": {
                "$all": [ObjectId(user_id_1), ObjectId(user_id_2)]
            },
            "participants": {"$size": 2}
        })


    # Lấy danh sách chat ===============================================================================================
    async def get_conversations_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        user_obj_id = ObjectId(user_id)
        query = {
            "participants.user_id": user_obj_id,
            "deleted_by.user_id": {"$ne": user_obj_id}
        }
        cursor = self.collection.find(query).sort("updated_at", -1)
        return await cursor.to_list(length=1000)


    # Ẩn cuộc trò chuyện ===============================================================================================
    async def hide_for_user(self, conversation_id: str, user_id: str) -> bool:

        delete_record = {
            "user_id": ObjectId(user_id),
            "deleted_at": datetime.utcnow()
        }

        await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$pull": {"deleted_by": {"user_id": ObjectId(user_id)}}}
        )

        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$push": {"deleted_by": delete_record}}
        )
        return result.modified_count > 0


    # hồi sinh đoạn chat ===============================================================================================
    async def resurrect_for_user(self, conversation_id: str, user_id: str) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$pull": {"deleted_by": {"user_id": ObjectId(user_id)}}}
        )
        return result.modified_count > 0