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

    async def get_public_by_ids(self, user_ids: set[ObjectId]) ->  list[Dict[str, Any]]:
        cursor = self.collection.find({"user_id": {"$in": list(user_ids)}})

        users = []
        async for user in cursor:
            users.append(user)

        print(f"Test: {users}")

        return users


    async def update_by_user_id(self, user_id: str, media_id: str) -> Dict[str, Any]:
        update =  await self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set":{"avatar": ObjectId(media_id)} }
        )
        user_profile = await self.collection.find_one(
            {"user_id": ObjectId(user_id)}
        )
        print(user_profile)
        return user_profile

    async def update_avatar(
            self,
            user_id: str,
            avatar_id: ObjectId
    ) -> Dict[str, Any]:
        await self.collection.update_one(
            {"user_id": ObjectId(user_id)},
            {"$set": {"avatar": avatar_id}}
        )

        return await self.collection.find_one(
            {"user_id": ObjectId(user_id)}
        )
