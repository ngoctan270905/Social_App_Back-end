from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from bson import ObjectId
from app.core.mongo_database import mongodb_client


class MediaRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("media")


    # Thêm mới media ===================================================================================================
    async def create(self, media_data: Dict[str, Any]) -> Dict[str, Any]:
     result = await self.collection.insert_one(media_data)
     media_data['_id'] = result.inserted_id
     return media_data


    # Lấy thông tin media theo id ======================================================================================
    async def get_by_id(self, media_id: ObjectId) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"_id": media_id})


    # Lấy nhiều media theo id ==========================================================================================
    async def get_by_ids(self, media_ids: list[ObjectId]) -> List[Dict[str, Any]]:
        cursor = self.collection.find({"_id": {"$in": list(media_ids)}})

        medias = []
        async for media in cursor:
            medias.append(media)

        return medias


    # Xóa nhiều media cùng lúc =========================================================================================
    async def delete_many(self, media_ids: List[str]):
        filter_query = {"_id": {"$in": [ObjectId(i) for i in media_ids]}}
        deleted = await self.collection.delete_many(filter_query)
        return deleted.deleted_count
