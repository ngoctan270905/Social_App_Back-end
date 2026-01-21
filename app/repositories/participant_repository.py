from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class ParticipantRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("participants")

    async def create_many(self, participants_data: List[Dict[str, Any]]):
        """Insert nhiều record cùng lúc"""
        if participants_data:
            await self.collection.insert_many(participants_data)

    async def get_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Lấy tất cả các record participant của một user"""
        cursor = self.collection.find({"user_id": ObjectId(user_id)})
        return await cursor.to_list(length=1000)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Tìm một record dựa trên query tùy ý"""
        return await self.collection.find_one(query)