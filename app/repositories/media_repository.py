from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class MediaRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("media")

    async def create(self, media_data: Dict[str, Any]) -> Dict[str, Any]:
     result = await self.collection.insert_one(media_data)
     media_data['_id'] = result.inserted_id
     return media_data

    async def get_by_id(self, media_id: ObjectId) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": media_id})

    async def get_by_ids(self, media_ids: set[ObjectId]) -> List[Dict[str, Any]]:
        print(f"đi vào đây")
        print(f"truyền vào media_ids: {media_ids}")
        cursor = self.collection.find({"_id": {"$in": list(media_ids)}})

        medias = []
        async for media in cursor:
            medias.append(media)
        print(f"Danh sasch media_ids: {medias}")

        return medias