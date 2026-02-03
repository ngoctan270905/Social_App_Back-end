from typing import Dict, Any, List, Optional
from bson import ObjectId
from app.core.mongo_database import mongodb_client

class NotificationRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("notifications")


    # Lưu thông báo vào DB =============================================================================================
    async def create(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        insert_result = await self.collection.insert_one(notification_data)
        notification_data["_id"] = insert_result.inserted_id
        return notification_data


    # Lấy danh sách thông báo ==========================================================================================
    async def get_by_recipient(self, recipient_id: str, limit: int = 20, cursor: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {"recipient_id": recipient_id}

        if cursor:
            query["_id"] = {"$lt": ObjectId(cursor)}
        
        cursor_obj = self.collection.find(query).sort("_id", -1).limit(limit)
        docs = []
        async for doc in cursor_obj:
            docs.append(doc)

        return docs