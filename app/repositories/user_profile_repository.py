from typing import Optional, List, Dict, Any
from bson import ObjectId
from app.core.mongo_database import mongodb_client
from app.schemas.auth import UserRegister

class UserProfileRepository:
    def __init__(self):
        self.db = mongodb_client.get_database()
        self.collection = self.db.get_collection("user_profiles")

    # Truy vấn DB thêm user_profile ====================================================================================
    async def create(self, user_profile_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.collection.insert_one(user_profile_data)
        user_profile_data["_id"] = result.inserted_id
        return user_profile_data

    async def get_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        profile = await self.collection.find_one({"user_id": ObjectId(user_id)})
        return profile

    async def update_by_user_id(self, user_id: str, data: dict):
        return await self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": data}
        )

