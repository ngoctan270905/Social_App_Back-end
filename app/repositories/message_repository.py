from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client
from app.schemas.message import MessageCreate


class MessageRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("messages")

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

    async def get_by_conversation(self, conversation_id: str, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        cursor = self.collection.find(
            {"conversation_id": ObjectId(conversation_id)}
        ).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)