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

    # async def get_by_conversation(self, conversation_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    #     cursor = self.collection.find(
    #         {"conversation_id": ObjectId(conversation_id)}
    #     ).sort("created_at", -1).skip(skip).limit(limit)
    #     result = []
    #     async for doc in cursor:
    #         result.append(doc)
    #
    #     return result

    async def get_by_conversation(
            self,
            conversation_id: str,
            cursor: Optional[str] = None,
            limit: int = 50
    ) -> List[Dict[str, Any]]:

        # 1. Tạo query filter
        query: Dict[str, Any] = {
            "conversation_id": ObjectId(conversation_id)
        }

        # 2. Nếu có cursor thì lấy message cũ hơn cursor đó
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

    async def delete_by_conversation_id(self, conversation_id: str) -> int:
        """
        Xóa tất cả tin nhắn thuộc về một cuộc trò chuyện.
        Trả về số lượng tin nhắn đã xóa.
        """
        result = await self.collection.delete_many({"conversation_id": ObjectId(conversation_id)})
        return result.deleted_count

    async def delete(self, message_id: str) -> bool:
        """
        Xóa document tin nhắn theo ID.
        """
        result = await self.collection.delete_one({"_id": ObjectId(message_id)})
        return result.deleted_count > 0

    async def get_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": ObjectId(message_id)})


