from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class NewRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("news")

    async def get_all_news(self) -> List[Dict[str, Any]]:
        news = []
        async for new in self.collection.find({"deleted_at": None}):
            news.append(new)
        return news


    async def create(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_new = await self.collection.insert_one(new_data)
        new_data["_id"] = insert_new.inserted_id
        return new_data


