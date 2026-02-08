from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client
from app.schemas.message import MessageCreate


class MessageRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("messages")


    # Thêm message mới =================================================================================================
    async def create(self, conversation_id: str, sender_id: str, content: str) -> Dict[str, Any]:
        doc = {
            "conversation_id": ObjectId(conversation_id),
            "sender_id": ObjectId(sender_id),
            "content": content,
            "created_at": datetime.utcnow()
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc


    # Lấy tin nhắn phân trang ==========================================================================================
    async def get_by_conversation(
            self,
            conversation_id: str,
            cursor: Optional[str] = None,
            limit: int = 50
    ) -> List[Dict[str, Any]]:

        query: Dict[str, Any] = {
            "conversation_id": ObjectId(conversation_id)
        }

        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}

        db_cursor = (
            self.collection
            .find(query)
            .sort("_id", -1)
            .limit(limit)
        )

        messages = []
        async for message in db_cursor:
            messages.append(message)

        return messages


    # Xóa tin nhắn =====================================================================================================
    async def delete(self, message_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count > 0


    # Lấy thông tin chi tiết 1 tin nhắn ===============================================================================
    async def get_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(message_id)})


